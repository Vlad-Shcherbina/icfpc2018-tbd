const simulator = require('./exec-trace-wrapped.js')
const fs = require('fs')

if (process.argv.length != 4) {
    console.log("usage: node ./trace.js [model] [trace]")
}
else {
    const [_node, _tracejs, modelfile, tracefile] = process.argv
    const model = fs.readFileSync(modelfile)
    const trace = fs.readFileSync(tracefile)
    simulator.execTrace(model, trace)
}
