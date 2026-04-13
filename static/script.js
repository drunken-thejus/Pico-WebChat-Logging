/**
 * script.js — Pico Chat
 *
 * Handles all WebSocket communication, message rendering,
 * active user list, and mini private chat windows.
 *
 * Fixes applied:
 *  - Single WebSocket instance (no duplicate from chat.html inline script)
 *  - XSS-safe DOM construction (no innerHTML with user content)
 *  - Reliable DOM selectors (class-based, not nth-child)
 *  - Auto-reconnect on disconnect
 *  - Enter key sends message in main chat
 *  - Connection status indicator
 */

const username = window.currentUser;


if (!username) {
    window.location.href = "/";
}

// ─── WebSocket Setup ──────────────────────────────────────────────────────────

let socket;
let reconnectTimer = null;
const RECONNECT_DELAY_MS = 3000;



function connect() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(`${protocol}://${window.location.host}/ws/${encodeURIComponent(username)}`);

    socket.onopen = () => {
        setConnectionStatus(true);
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
    };

    socket.onmessage = (event) => {
        let result;
        try {
            result = JSON.parse(event.data);
        } catch {
            console.error("Invalid message from server:", event.data);
            return;
        }

        if (result.type === "error") {
            alert(result.data.log || "An error occurred.");
            window.location.href = "/";
            return;
        }

        if (result.type === "active-users-list") {
            renderActiveUsers(result.data.users);
            return;
        }

        if (result.type === "message") {
            const { type, sender, message } = result.data;
            if (type === "public") {
                addPublicMessage(sender, message);
            } else if (type === "private") {
                openMiniChat(sender, message);
            }
        }
    };

    socket.onclose = () => {
        setConnectionStatus(false);
        // Attempt to reconnect
        reconnectTimer = setTimeout(() => {
            console.log("Reconnecting...");
            connect();
        }, RECONNECT_DELAY_MS);
    };

    socket.onerror = (err) => {
        console.error("WebSocket error:", err);
        socket.close(); // triggers onclose → reconnect
    };
}

function setConnectionStatus(connected) {
    const el = document.getElementById("conn-status");
    if (!el) return;
    el.textContent = connected ? "Connected" : "Reconnecting...";
    el.classList.toggle("disconnected", !connected);
}

// ─── Public Chat ──────────────────────────────────────────────────────────────

/**
 * Safely create and append a message bubble to the main chat.
 * Uses innerText throughout — never innerHTML with user content.
 */
function addPublicMessage(sender, message) {
    const box = document.getElementById("messages");
    const isOwn = sender === username;

    const bubble = document.createElement("div");
    bubble.className = "bubble " + (isOwn ? "right" : "left");

    if (!isOwn) {
        const nameEl = document.createElement("div");
        nameEl.className = "bubble-sender";
        nameEl.innerText = sender;
        bubble.appendChild(nameEl);
    }

    const textEl = document.createElement("div");
    textEl.innerText = message;
    bubble.appendChild(textEl);

    box.appendChild(bubble);
    box.scrollTop = box.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById("messageInput");
    const text = input.value.trim();
    if (!text) return;

    // Don't send if socket isn't open
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert("Not connected. Please wait a moment and try again.");
        return;
    }

    socket.send(JSON.stringify({ type: "public", message: text }));
    input.value = "";
}

// Send on Enter key
document.getElementById("messageInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

document.getElementById("send-btn").addEventListener("click", sendMessage);

// Set header username
const headerEl = document.getElementById("header-username");
if (headerEl) headerEl.innerText = `Logged in as ${username}`;

// ─── Active Users List ────────────────────────────────────────────────────────

function renderActiveUsers(users) {
    const container = document.getElementById("active-users");
    container.innerHTML = "";

    users.forEach(user => {
        if (user === username) return; // skip self

        const div = document.createElement("div");
        div.className = "user";

        const dot = document.createElement("div");
        dot.className = "dot";

        const name = document.createElement("span");
        name.innerText = user; // innerText — safe against XSS

        div.appendChild(dot);
        div.appendChild(name);
        // in renderActiveUsers, update the click handler
div.addEventListener("click", () => {
    openMiniChat(user);
    loadPrivateHistory(user);
    //load_pico_history()
    //await loadPicoHistory();  // ← add this
});

        container.appendChild(div);
    });
}

// ─── Mini Private Chat ────────────────────────────────────────────────────────

/**
 * Opens a private mini-chat window for `user`.
 * If already open, just appends the incoming message (if any).
 * Uses class-based selectors and innerText — no fragile nth-child, no innerHTML.
 */
function openMiniChat(user, incomingMessage = null) {
    const container = document.getElementById("mini-chats-container");
    const chatId = `mini-chat-${CSS.escape(user)}`;

    let chatBox = document.getElementById(chatId);

    if (!chatBox) {
        chatBox = document.createElement("div");
        chatBox.className = "mini-chat";
        chatBox.id = chatId;

        // ── Header ──
        const header = document.createElement("div");
        header.className = "mini-header";

        const headerName = document.createElement("span");
        headerName.innerText = user;

        const closeBtn = document.createElement("span");
        closeBtn.className = "mini-close";
        closeBtn.textContent = "\u00D7"; // × — proper Unicode, no encoding issues
        closeBtn.title = "Close";
        closeBtn.addEventListener("click", () => chatBox.remove());

        header.appendChild(headerName);
        header.appendChild(closeBtn);

        // ── Messages area ──
        const messagesDiv = document.createElement("div");
        messagesDiv.className = "mini-messages"; // reliable class selector

        // ── Input area ──
        const inputArea = document.createElement("div");
        inputArea.className = "mini-input";

        const input = document.createElement("input");
        input.type = "text";
        input.placeholder = "Message...";

        const sendBtn = document.createElement("button");
        sendBtn.innerText = "Send";

        function sendPrivate() {
            const msg = input.value.trim();
            if (!msg) return;

            if (!socket || socket.readyState !== WebSocket.OPEN) {
                alert("Not connected. Please wait.");
                return;
            }

            socket.send(JSON.stringify({
                type: "private",
                receiver: user,
                message: msg
            }));

            // Show own message in the mini-chat
            appendMiniMessage(messagesDiv, msg, "right");
            input.value = "";
        }

        sendBtn.addEventListener("click", sendPrivate);
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendPrivate();
        });

        inputArea.appendChild(input);
        inputArea.appendChild(sendBtn);

        chatBox.appendChild(header);
        chatBox.appendChild(messagesDiv);
        chatBox.appendChild(inputArea);

        container.appendChild(chatBox);
    }

    // Append the incoming message if provided
    if (incomingMessage) {
        const messagesDiv = chatBox.querySelector(".mini-messages");
        appendMiniMessage(messagesDiv, incomingMessage, "left");
    }
}

/**
 * Safely appends a bubble to a mini-chat messages div.
 */
function appendMiniMessage(messagesDiv, text, side) {
    const bubble = document.createElement("div");
    bubble.className = `mini-bubble ${side}`;
    bubble.innerText = text; // innerText — safe
    messagesDiv.appendChild(bubble);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// ─── Init ─────────────────────────────────────────────────────────────────────
// ─── Load History on Page Load ───────────────────────────────────────────────

async function loadPublicHistory() {
    try {
        const res = await fetch("/api/history/public", {
    credentials: "include"
});
        const messages = await res.json();
        messages.forEach(({ username: sender, message }) => {
            addPublicMessage(sender, message);
        });
    } catch (e) {
        console.error("Failed to load public history:", e);
    }
}

async function loadPrivateHistory(otherUser) {
    try {
        let url;

        if (otherUser === "PICO") {
            url = "/api/history/pico";
        } else {
            url = `/api/history/private/${encodeURIComponent(otherUser)}`;
        }

        const res = await fetch(url, {
    credentials: "include"
});
        const data = await res.json();

        const chatId = `mini-chat-${CSS.escape(otherUser)}`;
        let chatBox = document.getElementById(chatId);

        if (!chatBox) openMiniChat(otherUser);
        chatBox = document.getElementById(chatId);

        const messagesDiv = chatBox.querySelector(".mini-messages");
        messagesDiv.innerHTML = ""; // clear old messages

        if (otherUser === "PICO") {
            const history = data.chat_history || [];

            history.forEach(msg => {
                // Skip personality/system prompts
                if (
                    msg.content.length > 300 ||      // long prompt
                    msg.content.includes("You are Pico") // system text
                ) return;

                const side = msg.role === "user" ? "right" : "left";
                appendMiniMessage(messagesDiv, msg.content, side);
            });

        } else {
            data.forEach(({ sender, message }) => {
                const side = sender === username ? "right" : "left";
                appendMiniMessage(messagesDiv, message, side);
            });
        }

    } catch (e) {
        console.error("Failed to load history:", e);
    }
}
async function loadPicoHistory() {

    try {
        const res = await fetch("/api/history/pico");
        const data = await res.json();
        const history = data.chat_history || [];

        // open pico mini chat
        openMiniChat("Pico");
        const chatBox = document.getElementById(`mini-chat-${CSS.escape("Pico")}`);
        const messagesDiv = chatBox.querySelector(".mini-messages");

        history.forEach(({ role, content }) => {
            // skip system prompts (long messages injected into history)
            if (content.length > 300 && role === "user") return;
            const side = role === "user" ? "right" : "left";
            appendMiniMessage(messagesDiv, content, side);
        });
    } catch (e) {
        console.error("Failed to load pico history:", e);
    }
}

// ─── Init ─────────────────────────────────────────────────────────────────────

async function load_pico_history(){
    await loadPicoHistory();
}

async function init() {
    await loadPublicHistory();
    //await loadPicoHistory();
    // private history loads when user clicks on someone in the active users list
    connect();
}

init();
