/*
merge_equal_td.js is generated from merge_equal_td.ts using the following command:

cd production/dashboard/static
tsc

Don't edit merge_equal_td.js manually.
It's under version control to simplify deployment.
Remember to update it when changing merge_equal_td.ts.
*/
'use strict';
function mergeEqualTd(table, columnGroups) {
    let t = [];
    for (let row of table.getElementsByTagName('tr')) {
        t.push([...row.getElementsByTagName('td')]);
    }
    let toMerge = [];
    for (let columnGroup of columnGroups) {
        for (let i = 0; i < t.length;) {
            let j = i + 1;
            while (true) {
                if (j >= t.length) {
                    break;
                }
                let eq = true;
                for (let column of columnGroup) {
                    if (column >= t[i].length ||
                        column >= t[j].length ||
                        t[i][column].innerHTML != t[j][column].innerHTML) {
                        eq = false;
                        break;
                    }
                }
                if (!eq) {
                    break;
                }
                j++;
            }
            if (j != i + 1) {
                for (let column of columnGroup) {
                    toMerge.push({ column: column, row1: i, row2: j });
                }
            }
            i = j;
        }
    }
    for (let e of toMerge) {
        t[e.row1][e.column].rowSpan = e.row2 - e.row1;
        for (let i = e.row1 + 1; i < e.row2; i++) {
            let elem = t[i][e.column];
            elem.parentNode.removeChild(elem);
        }
    }
}
