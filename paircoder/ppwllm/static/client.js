window.addEventListener("DOMContentLoaded", () =>{
    const websy = new WebSocket(`ws://${window.location.host}/ws/chat/lobby/`);
    document.querySelector("#submit").addEventListener("click", () => {
        console.log("got in") 
        const ai_intent = document.querySelector("#chat_window").value
        const user_msg = document.querySelector("#user_msg").value
        websy.send(JSON.stringify({message: user_msg,
                                   ai_intent: ai_intent}))
    });
    websy.onmessage = ({ data }) => {
        const json_data = JSON.parse(data)
        console.log(json_data)
        document.querySelector("#chat_window").value += `
    ${ai_intent}
                                Your Feedback: ${user_msg}
                    Update Intent: ${json_data['response']}
        `
        }
    });