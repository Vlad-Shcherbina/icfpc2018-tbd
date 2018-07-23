function fetch_db(url, id, desc_id) {
    const elem = $(id)
    const desc = $(desc_id)
    $.ajax(url).done(function(d) {
        let {columns, data} = JSON.parse(d)
        var map = new Function(...columns, `return {${columns.join(', ')}}`)
        let cur_id = -1
        const bests = {}
        const defaults = {}
        data = data.map(row => map(...row))
        data.forEach(function(row, i) {
            const {energy, id, trace_id, status, scent} = row
            row.first = cur_id != id
            cur_id = id
            if (energy && (!bests[id] || bests[id].energy > energy)) bests[id] = {trace_id, energy}
            if (scent == "their default" && status == "DONE") defaults[id] = energy
            let lookahead = 1
            while(data[i+lookahead] && data[i+lookahead].id == id) lookahead++
            row.lookahead = lookahead
        })
        let total_score = 0
        data.forEach(function(row) {
            row.is_best = bests[row.id] && bests[row.id].trace_id == row.trace_id
            row.score = best_scores[row.name.toLowerCase()] && row.energy ? calc_score(row.stats.R, defaults[row.id], row.energy, best_scores[row.name.toLowerCase()])  : undefined
            if (row.score && row.is_best) total_score += row.score
        })
        desc.html("total score: " + total_score)
        
        elem.html(data.map(make_row).join('\n'))
    })
}
function calc_score(R, energy_dflt, energy_team, energy_best) {
    if (energy_best >= energy_dflt) energy_best = energy_dflt - 1
    if (energy_team >= energy_dflt) energy_team = energy_dflt
    return Math.floor(Math.floor(Math.log2(R)) * 1000 * (energy_dflt - energy_team) / (energy_dflt - energy_best))
}
// when live standings include all scores:
// go to https://icfpcontest2018.github.io/full/live-standings.html, paste function in console, do JSON.stringify(get_all_scores())
function get_all_scores() {
    const mins = {}
    Array.from(document.getElementsByTagName('h3')).filter(({id}) => id.startsWith("problem-")).forEach(elem => {
        mins[elem.id.slice(8)] = Math.min(...Array.from(elem.nextElementSibling.getElementsByTagName("tbody")[0].getElementsByTagName("tr")).map(({children}) => +children[1].innerText))
    })
    return mins
}
const best_scores = {"fa001":705904,"fa004":1195558,"fa008":1411344,"fa009":887894,"fa011":486302,"fa017":1261864,"fa019":1805038,"fa020":1837446,"fa022":15089794,"fa028":6068434,"fa030":9357902,"fa032":10829100,"fa034":12152988,"fa040":23688448,"fa044":41855754,"fa046":73423520,"fa047":16217042,"fa052":33902646,"fa053":28234728,"fa055":29755878,"fa059":142818882,"fa061":167497672,"fa063":167101036,"fa076":207993772,"fa080":337017292,"fa084":368968950,"fa092":732993162,"fa094":491884810,"fa095":322998372,"fa096":2776865428,"fa097":725815572,"fa098":1101125642,"fa099":1416033116,"fa101":367431948,"fa102":747264624,"fa105":9167683852,"fa108":3872069880,"fa118":1708136212,"fa121":1315395894,"fa125":2022853626,"fa128":3251772076,"fa132":2299513354,"fa136":2707511282,"fa140":3505405640,"fa143":3564546790,"fa156":3702817400,"fa162":27426784824,"fa164":78774958386,"fa165":62137142624,"fa166":28108517356,"fa167":43007548492,"fa169":37916909484,"fa174":46790631766,"fa181":235839780158,"fd001":382175,"fd004":389157,"fd005":391168,"fd011":388023,"fd014":399103,"fd017":398533,"fd019":1126324,"fd022":1334404,"fd025":1173724,"fd027":1394704,"fd033":1392019,"fd035":1345774,"fd036":1407634,"fd039":1385404,"fd041":1280359,"fd042":6833090,"fd044":5209146,"fd048":4875204,"fd051":5500026,"fd056":10358764,"fd058":28106246,"fd059":37215731,"fd071":17558743,"fd072":42781964,"fd075":71620074,"fd076":63653453,"fd090":303233258,"fd094":358401471,"fd096":608378525,"fd099":780504924,"fd102":116823824,"fd103":268895447,"fd104":401021697,"fd106":669774018,"fd107":470413360,"fd110":331715419,"fd111":525031114,"fd112":326574194,"fd113":222074045,"fd120":1047015523,"fd121":552122212,"fd122":1505938934,"fd124":126026092,"fd127":466427063,"fd131":1607444527,"fd136":964107336,"fd137":11435304842,"fd139":2477780991,"fd141":923165203,"fd145":6896388897,"fd146":1768793810,"fd151":2649535645,"fd152":3441690933,"fd156":891907476,"fd163":5420236038,"fd167":5918113954,"fd168":4177681532,"fd171":6796115151,"fd173":73603001570,"fd175":11387173862,"fd176":39104385220,"fd179":28457597546,"fd181":88173509091,"fd183":29542524313,"fr001":1836006,"fr005":1513963,"fr009":1685574,"fr014":16425490,"fr016":1740694,"fr019":1948774,"fr021":5185392,"fr023":7723762,"fr024":17293280,"fr029":25564328,"fr042":95977066,"fr046":197531174,"fr047":243026174,"fr048":263403896,"fr050":241442874,"fr054":419500282,"fr055":512117717,"fr058":313125068,"fr063":839252414,"fr067":1552132244,"fr078":5903585446,"fr083":2056777364,"fr085":6599760260,"fr087":29387767940,"fr098":10630903898,"fr100":84985134094,"fr102":201035168442}
             
let total_score = 0
function make_row({id,	name,	has_src,	has_tgt,	stats,	prob_inv_id,	trace_id,	scent,	status,	energy,	trace_inv_id,	has_data, extra, first, lookahead, is_best, score}) {
    const linkify = (p,f) => `<a href=/${p}/${f}>/${p}/${f}</a>`
    const vis = tp => ` (<a href="/vis_model/${id}?which=${tp}">vis ${tp}</a>)`
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
        `${(extra||{}).solver_time|0}s+${(extra||{}).pyjs_time|0}s`,
        score == undefined ? "" : score
    ];
    return `<tr>${cols.map(render_td).join('')}</tr>`
}
