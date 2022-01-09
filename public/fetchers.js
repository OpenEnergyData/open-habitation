// class HouseInfo {
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
//     constructor(
//         readonly address: string,
//         readonly plant_type: string | undefined,
//         readonly total_plower: number | undefined,
//         readonly angle: number | undefined,
//         readonly aspect: number | undefined,
//         readonly mounting_place: string | undefined,
//         readonly yearly_production: number | undefined,
//         readonly space_heating: string | undefined,
//         readonly hot_water: string | undefined,
//         readonly eco_rating: string | undefined
//     ){}
// }
/**
 *
 * @param {string} url URL to the resource
 * @returns Promise with the parsed JSON data from the response if resolved
 */
const getResource = (url) => __awaiter(void 0, void 0, void 0, function* () {
    const response = yield fetch(url);
    if (response.status !== 200) {
        throw new Error(`Resource could not be fetched. Status: ${response.status}`);
    }
    const data = yield response.json();
    return data;
});
/**
 *
 * @param {string} url URL to the resource for the house info
 * @returns {Promise<object>} Promise of an object containing info about the house
 */
const getHouseInfo = (url) => __awaiter(void 0, void 0, void 0, function* () {
    const info = yield getResource(url);
    return info;
});
function syntaxHighlight(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'key';
            }
            else {
                cls = 'string';
            }
        }
        else if (/true|false/.test(match)) {
            cls = 'boolean';
        }
        else if (/null/.test(match)) {
            cls = 'null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}
// /**
//  *
//  * @param {string} production_url URL to the resource for the production info
//  * @param {string} heating_url URL to the resource for the heating info
//  * @returns {object} object containing info about the house
//  */
// function getHouseInfo(production_url: string, heating_url: string): object {
//     let info : any = {};
//     getResource(production_url).then(data => {
//         info.production = data;
//     }).catch(err => {
//         info.production = undefined;
//         console.log("Production resource not found.");
//     });
//     getResource(heating_url).then(data => {
//         info.heating = data;
//     }).catch(err => {
//         info.heating = undefined;
//         console.log("Heating resource not found.");
//     });
//     return info;
// }
export { getHouseInfo, syntaxHighlight };
