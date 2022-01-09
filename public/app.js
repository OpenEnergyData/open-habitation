import { getHouseInfo, syntaxHighlight } from "./fetchers.js";
const HOUSE_QUERY_BASE_URL = "/api/houseinfo";
// console.log(new Date().toISOString());
let rows = []; // rows of the table
const buttonEl = document.querySelector("#search_button");
// const tbodyEl = document.querySelector("tbody")!;
const formEl = document.querySelector("form");
const searchErrorEl = document.getElementById("search_error");
const jsonDisplayEl = document.getElementById("json-display");
function houseQuery(e) {
    e.preventDefault();
    let formData = new FormData(formEl);
    console.log(formData.get("address"));
    // check validity of parameters
    let address = formData.get("address");
    let angle_str = formData.get("angle");
    let aspect_str = formData.get("aspect");
    let angle;
    let aspect;
    let mountingplace = formData.get("mountingplace");
    if (angle_str == "") {
        angle = undefined;
    }
    else {
        angle = Number(angle_str);
    }
    if (aspect_str == "") {
        aspect = undefined;
    }
    else {
        aspect = Number(aspect_str);
    }
    if (address === "") {
        searchErrorEl.innerText = "Address field is required.";
        return;
    }
    else if ((angle !== undefined) && ((angle < 0) || (angle > 90) || (isNaN(angle)))) {
        searchErrorEl.innerText = "PV angle must be a number between 0 and 90.";
        return;
    }
    else if ((aspect !== undefined) && ((aspect < -180) || (aspect > 180) || (isNaN(aspect)))) {
        console.log("aspect: ", aspect);
        searchErrorEl.innerText = "PV orientation (aspect) must be a number between -180 and 180.";
        return;
    }
    else {
        searchErrorEl.innerText = "";
    }
    ;
    // compose query string
    let queryString = `?address=${address}`;
    queryString += `&angle=${angle}`;
    queryString += `&aspect=${aspect}`;
    // queryString += `&mountingplace=${mountingplace}`
    let url = HOUSE_QUERY_BASE_URL + queryString;
    // console.log("URL: ", url);
    // console.log(formData.values());
    // // console.log(form.getAll());
    // console.log(formData.entries());
    // console.log(formData.get("angle"));
    // console.log(typeof formData.get("angle"));
    // if(formData.get("angle")){
    //     console.log("true")
    // }
    // console.log(formData.keys());
    // for(var pair of formData.entries()){
    //     if(pair[1]){
    //         console.log(pair[0], pair[1])
    //     } else {
    //         console.log("No value entered for input", pair[0])
    //     }
    // }
    // make get request to API
    getHouseInfo(url).then((info) => {
        // console.log(JSON.stringify(info));
        jsonDisplayEl.innerHTML = syntaxHighlight(JSON.stringify(info, null, 4));
        // tbodyEl.innerHTML = "";
        // if (rows.length >= 10) {
        //     rows.pop()
        // }
        // let newrow: string = "<tr>";
        // Object.keys(info).forEach((k, i) => {
        //     let value = info[k]
        //     if (value === null) {
        //         value = "-"
        //     }
        //     newrow += `<td>${value}</td>`
        // })
        // newrow += "</tr>";
        // rows.push(newrow);
        // rows.forEach(row => {
        //     tbodyEl.innerHTML += row;
        // })
    }).catch(err => {
        console.log(err);
        console.log("No info found for that address.");
    });
}
buttonEl.addEventListener("click", houseQuery);
// if(button){
//     button.addEventListener("click", houseQuery);
// }
// const getProduction = (url="../resources/production.json") => {
//     getResource(url).then(data => {
//         return data
//     }).catch(err => {
//         console.log(err)
//     })
// }
// getResource("../resources/production.json").then(data => {
//     console.log(data);
// }).catch(err => {
//     console.log(err)
// })
// fetch("../resources/production.json").then((response) => {
//     if(response.status===200){
//         return response.json()
//     } else {
//         throw new Error("cannot fetch data.");
//     }
// }).then((data) => {
//     console.log(data);
// }).catch((err) => {
//     console.log(err);
// })
