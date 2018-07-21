'''
Utility to locally run solvers that conform to solver_interface.py
for debugging purposes.
'''

from importlib.util import find_spec
if __name__ == '__main__' and find_spec('hintcheck'):
    import hintcheck
    hintcheck.monkey_patch_named_tuple_constructors()

import zlib
import sys
import logging
logger = logging.getLogger(__name__)

from production import db
from production import solver_interface
from production.pyjs_emulator.run import run_full as pyjs_run_full
from production.all_solvers import ALL_SOLVERS


def main():
    if len(sys.argv) < 2 :
        print('Usage:')
        print('    python -m production.solver_runner <solver> [<solver args>...]')
        print(f'where <solver> is one of {ALL_SOLVERS.keys()}')
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    conn = db.get_conn()
    cur = conn.cursor()

    solver = ALL_SOLVERS[sys.argv[1]](sys.argv[2:])
    logger.info(f'Solver scent: {solver.scent()!r}')

    cur.execute('''
        SELECT problems.id, problems.name
        FROM problems
        WHERE problems.name LIKE 'F%'
    ''')
    problem_ids = []
    for id, name in cur:
        if solver.supports(solver_interface.ProblemType.from_name(name)):
            problem_ids.append(id)
    logger.info(f'Problems to solve: {problem_ids}')

    for problem_id in problem_ids:
        logger.info('-' * 50)
        cur.execute(
            'SELECT name, src_data, tgt_data FROM problems WHERE id = %s',
            [problem_id])
        [problem_name, src_data, tgt_data] = cur.fetchone()
        logger.info(f'Solving problem/{problem_id} ({problem_name})...')

        if src_data is not None:
            src_data = zlib.decompress(src_data)
        if tgt_data is not None:
            tgt_data = zlib.decompress(tgt_data)

        sr = solver.solve(problem_name, src_data, tgt_data)
        logging.info(f'extra: {sr.extra}')
        if isinstance(sr.trace_data, solver_interface.Pass):
            logging.info('Solver passed')
        elif isinstance(sr.trace_data, solver_interface.Fail):
            logging.warning('Solver failed')
        else:
            logging.info('Solver produced a trace, checking with pyjs...')
            er = pyjs_run_full(src_data, tgt_data, sr.trace_data)
            logging.info(er)

    logger.info('All done')


if __name__ == '__main__':
    if 'hintcheck' in globals():
        hintcheck.hintcheck_all_functions()
    main()
