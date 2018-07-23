function fetch_db(url, id) {
    const elem = $(id)
    $.ajax(url).done(function(d) {
        let {columns, data} = JSON.parse(d)
        var map = new Function(...columns, `return {${columns.join(', ')}}`)
        const bests = {}
        data.forEach(f => {
            const {energy,id,trace_id} = map(...f)
            if (energy != undefined) {
                if (!bests[id] || bests[id].energy > energy) bests[id] = {trace_id, energy}
            }
        })
        let cur_id = -1
        elem.html(data.map((row, i) => {
            const first = cur_id != row[0]
            cur_id = row[0]
            let lookahead = 1
            while(data[i+lookahead] && data[i+lookahead][0] == row[0]) lookahead++
            return make_row(map(...row), bests, first, lookahead)
        }).join('\n'))
        window.bests = bests
    })
}
function make_row({id,	name,	has_src,	has_tgt,	stats,	prob_inv_id,	trace_id,	scent,	status,	energy,	trace_inv_id,	has_data, extra}, bests, first, lookahead) {
    const linkify = (p,f) => `<a href=/${p}/${f}>/${p}/${f}</a>`
    const vis = tp => ` (<a href="/vis_model/${id}?which=${tp}">vis ${tp}</a>)`
    const is_best = bests[id] && bests[id].trace_id == trace_id
    function render_td(param) {
        const {text, bold, rowspan} = typeof param == "object" ? param : { text: param }
        
        if (rowspan && !first) return ""
        return `<td rowspan=${rowspan ? lookahead : 1} style="${bold?"font-weight: bold;":''}${first?"border-top: 2px solid #aaa;":''}">${text}</td>`
    }
    
    const cols = [
        {text: linkify('inv', prob_inv_id), rowspan: true},
        {text: linkify('problem', id) + (has_src?vis('src'):'') + (has_tgt?vis('tgt'):''), rowspan: true},
        {text: name, rowspan: true},
        {text: Object.keys(stats).map(f=>`${f}: ${stats[f]}`).join(', '), rowspan: true},
        linkify('trace', trace_id) + ` (<a href="/vis_trace/${trace_id}">vis</a>)`,
        {text: status, bold: is_best},
        {text: energy, bold: is_best},
        {text: scent, bold: is_best},
        linkify('inv', trace_inv_id),
        `${extra.solver_time|0}s+${extra.pyjs_time|0}s`,
    ];
    return `<tr>${cols.map(render_td).join('')}</tr>`
}
