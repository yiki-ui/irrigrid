const turf = require('@turf/turf');
const ring = [[29.63, -1.50], [29.63, -1.49], [29.64, -1.49], [29.64, -1.50], [29.63, -1.50]];
const poly = turf.polygon([ring]);
console.log(turf.area(poly));
