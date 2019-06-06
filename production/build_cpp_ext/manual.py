import distutils.sysconfig
import hashlib
import importlib.machinery
import json
import logging
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pybind11


logger = logging.getLogger(__name__)


@dataclass
class BuildStep:
    inputs: List[str]
    output: str
    command: List[str]

    input_hashes: Optional[Dict[str, str]] = None

    def compute_input_hashes(self):
        assert self.input_hashes is None
        self.input_hashes = {f: file_hash(f) for f in self.inputs}

    def meta(self):
        return Path(self.output + '.meta')

    def need_rebuild(self):
        m = self.meta()
        if not m.exists():
            return True

        if not Path(self.output).exists():
            return True

        with m.open() as fin:
            m = json.load(fin)

        if m.pop('command') != self.command:
            return True
        if m.pop('input_hashes') != self.input_hashes:
            return True
        if m.pop('output_hash') != file_hash(self.output):
            return True

        assert not m, m
        return False

    def create_meta(self):
        m = dict(
            command=self.command,
            input_hashes=self.input_hashes,
            output_hash=file_hash(self.output))
        with self.meta().open('w') as fout:
            json.dump(m, fout, indent=4)


def file_hash(filename):
    return hashlib.sha1(Path(filename).read_bytes()).hexdigest()


def msvc_build_steps(*, name, sources, headers, release, build_dir, include_dirs, extension):
    lib_path = os.path.join(sys.exec_prefix, 'libs')

    # Work around
    # https://github.com/pypa/pip/issues/6582#issuecomment-500151425
    lib_path = lib_path.lower()
    include_dirs = [d.lower() for d in include_dirs]

    cmd = [
        'cl.exe',
        '/nologo',
        '/c',  # without linking
        '/Ox' if release else '/Od',
        '/W3',  # TODO: W4?
        '/MD' if release else '/MDd',  # multithreaded DLL
        '/std:c++latest',
        '/EHsc',
        '/diagnostics:caret',
        '/Zi',  # generate complete debugging information
    ]
    for d in include_dirs:
        cmd.append('-I' + d)
    if release:
        cmd.append('/GL')  # whole program optimization
    objs = []
    compile_steps = []
    for source in sources:
        obj = str(build_dir / source.replace('.cpp', '.obj'))
        objs.append(obj)
        compile_steps.append(BuildStep(
            command=[*cmd, '/Tp' + source, '/Fo' + obj],
            inputs=[source, *headers],  # TODO: only headers that are actually included
            output=obj))

    cmd = [
        'link.exe',
        '/nologo',
        '/INCREMENTAL:NO',
        '/DLL',
        '/MANIFEST:EMBED,ID=2',
        '/MANIFESTUAC:NO',
        '/DEBUG',
        f'/LIBPATH:{lib_path}',
        f'/EXPORT:PyInit_{name}',
        f'/OUT:{extension}',
        f'/IMPLIB:{build_dir}/{name}.lib',
    ]
    if release:
        cmd.append('/LTCG')  # link-time code generation
    cmd += objs
    link_step = BuildStep(
        command=cmd,
        inputs=objs,
        output=extension)

    return compile_steps, link_step


def gcc_build_steps(*, name, sources, headers, release, build_dir, include_dirs, extension):
    cmd = [
        'g++',
        '-g',  # produce debugging information
        '-O3' if release else '-O0',
        '-march=native',
        '-Wall',
        '-fPIC',  # emit position-independent code
        '-std=c++17',
        '-fvisibility=hidden',
    ]
    for d in include_dirs:
        cmd.append('-I' + d)
    if release:
        cmd.append('-flto')
    else:
        cmd.append('-D_GLIBCXX_DEBUG')
        cmd.append('-D_GLIBCXX_DEBUG_PEDANTIC')

    objs = []
    compile_steps = []
    for source in sources:
        obj = str(build_dir / source.replace('.cpp', '.o'))
        objs.append(obj)
        compile_steps.append(BuildStep(
            command=[*cmd, '-c', source, '-o', obj],
            inputs=[source, *headers],  # TODO: only headers that are actually included
            output=obj))

    cmd = [
        'g++',
        '-shared',
        '-Wl,-z,relro',
        '-fvisibility=hidden',
        '-o', extension,
    ]
    cmd += objs
    if release:
        cmd.append('-flto')

    link_step = BuildStep(
        command=cmd,
        inputs=objs,
        output=extension)

    return compile_steps, link_step


def build_extension(caller_file, name, sources, headers, release):
    cur_dir = os.getcwd()
    try:
        os.chdir(os.path.dirname(caller_file))

        if release:
            build_dir = Path('build2/release')
        else:
            build_dir = Path('build2/debug')
        build_dir.mkdir(parents=True, exist_ok=True)

        include_dirs = [
            distutils.sysconfig.get_python_inc(),
            pybind11.get_include(user=False),
            pybind11.get_include(user=True),
        ]
        extension = name + importlib.machinery.EXTENSION_SUFFIXES[0]

        if platform.system() == 'Windows':
            compile_steps, link_step = msvc_build_steps(
                name=name, sources=sources, headers=headers,
                release=release, build_dir=build_dir, include_dirs=include_dirs,
                extension=extension)
        else:
            compile_steps, link_step = gcc_build_steps(
                name=name, sources=sources, headers=headers,
                release=release, build_dir=build_dir, include_dirs=include_dirs,
                extension=extension)

        # TODO: Run compile steps in parallel. What to do with error messages?
        for step in compile_steps:
            step.compute_input_hashes()
            if not step.need_rebuild():
                logger.info(f'{step.output} is already up-to-date')
                continue
            start = time.time()
            subprocess.check_call(step.command)
            logger.info(f'compiling {step.output} took {time.time() - start:.2f} s')
            step.create_meta()

        step = link_step
        step.compute_input_hashes()
        if not step.need_rebuild():
            logger.info(f'{step.output} is already up-to-date')
        else:
            start = time.time()
            subprocess.check_call(step.command)
            logger.info(f'linking {step.output} took {time.time() - start:.2f} s')
            step.create_meta()

        for suffix in importlib.machinery.EXTENSION_SUFFIXES:
            e2 = name + suffix
            if e2 != extension:
                e2 = Path(e2)
                if e2.exists():
                    e2.unlink()

    finally:
        os.chdir(cur_dir)

    # Delete compiler config file used by du.py,
    # to ensure that if we later switch to TBD_BUILD_METHOD=distutils,
    # it will rebuild the extension.
    this_module = os.path.abspath(__file__)
    config_path = os.path.join(
        os.path.dirname(this_module),
        '_compiler_config.json')
    if os.path.exists(config_path):
        os.remove(config_path)
