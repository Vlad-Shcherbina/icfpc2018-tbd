const simulator = require('./exec-trace-wrapped.js')
const fs = require('fs')

function getArgs(func) {
    // thanks google
  // First match everything inside the function argument parens.
  var args = func.toString().match(/(function\s)?.*?\(([^)]*)\)/)[2];
 
  // Split the arguments string into an array comma delimited.
  return args.split(',').map(function(arg) {
    // Ensure no inline comments are parsed and trim the whitespace.
    return arg.replace(/\/\*.*\*\//, '').trim();
  }).filter(function(arg) {
    // Ensure no undefined values are added.
    return arg;
  });
}


if (process.argv.length < 4 || process.argv.length > 5) {
}
const [_node, _tracejs, cmd, ...rest] = process.argv
const cmds = {
    full: function(src, tgt, trace) {
        simulator.execTraceFull(...[src, tgt, trace].map(name => name == "None" ? undefined : fs.readFileSync(name)))
    },
    lgtn(model, trace) {
        simulator.execTrace(model, trace)
    },
    help() {
        console.log("usage: node ./trace.js [cmd]")
        for(const cmd in cmds) {
            console.log("              trace.js", cmd, ...getArgs(cmds[cmd]).map(f=>`[${f}]`))
        }
    }
}
if (cmds[cmd]) cmds[cmd](...rest)
else cmds.help()
