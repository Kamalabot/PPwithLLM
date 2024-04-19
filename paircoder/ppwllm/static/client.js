window.addEventListener("DOMContentLoaded", () =>{
    const websy = new WebSocket(`ws://${window.location.host}/ws/chat/{{chlng_id}}/`);
    document.querySelector("#submit").addEventListener("click", () => {
        console.log("got in") 
        const intent = document.querySelector("#chat_window").value
        const user_msg = document.querySelector("#user_msg").value
        websy.send(JSON.stringify({usr_msg: user_msg,
                                   intent: intent}))
    });
    websy.onmessage = ({ data }) => {
        const json_data = JSON.parse(data)
        console.log(json_data)
        document.querySelector("#chat_window").value += `
    ${intent}
                                Your Feedback: ${user_msg}
                    Update Intent: ${json_data['response']}
        `
        }
    });