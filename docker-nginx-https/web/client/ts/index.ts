import "core-js/stable";
import "regenerator-runtime/runtime";

let root = document.getElementById("root");

function printLine(line: string) {
    let p = document.createElement("p");
    p.innerText = line;
    root.appendChild(p);
    window.scrollTo(0, document.body.scrollHeight);
}

let ws = new WebSocket(`ws://${location.host}/certbot/${location.hostname}`);
ws.onmessage = event => {
    printLine(event.data)
};

function delay(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function checkHttps() {
    return new Promise((resolve, reject) => {
        let request = new XMLHttpRequest();
        request.onload = function () {
            resolve(request.response);
        };
        request.onerror = function () {
            reject();
        };
        request.open("GET", "", true);
        request.send();
    });
}

async function refresh() {
    while (true) {
        await delay(1000);
        try {
            await checkHttps();
        } catch (error) {
            location.reload();
        }
    }
}

refresh();
