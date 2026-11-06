const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const chat = document.getElementById("chat");
const newChatButton = document.getElementById("new-chat");
const historyContainer = document.getElementById("chat-history");
const clearHistoryButton = document.getElementById("clear-history");
const sendButton = document.getElementById("send-button");

const memoryDialog = document.getElementById("memory-dialog");
const memoryInput = document.getElementById("memory-input");
const openMemoryButton = document.getElementById("open-memory");
const closeMemoryButton = document.getElementById("close-memory");
const saveMemoryButton = document.getElementById("save-memory");
const clearMemoryButton = document.getElementById("clear-memory");

const STORAGE_KEY = "saraChats";
const MEMORY_KEY = "saraUserMemory";
const MAX_SAVED_CHATS = 40;

let conversationHistory = [];
let savedChats = loadSavedChats();
let currentChatId = createChatId();
let isSending = false;
let userMemory = loadMemory();

function createChatId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function loadSavedChats() {
    try {
        const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
        return Array.isArray(parsed) ? parsed.filter(c => c && Array.isArray(c.messages)) : [];
    } catch (error) {
        console.warn("Could not read saved chats:", error);
        return [];
    }
}

function loadMemory() {
    try {
        return localStorage.getItem(MEMORY_KEY) || "";
    } catch (error) {
        console.warn("Could not load memory:", error);
        return "";
    }
}

function saveMemory() {
    const newMemory = memoryInput.value.trim().slice(0, 5000);
    try {
        if (newMemory) localStorage.setItem(MEMORY_KEY, newMemory);
        else localStorage.removeItem(MEMORY_KEY);
        userMemory = newMemory;
        memoryDialog.close();
        showToast("SARA Memory saved in this browser.");
    } catch (error) {
        console.error("Could not save memory:", error);
        showToast("Could not save memory. Browser storage may be full.");
    }
}

openMemoryButton.addEventListener("click", () => {
    memoryInput.value = userMemory;
    memoryDialog.showModal();
});
closeMemoryButton.addEventListener("click", () => memoryDialog.close());
saveMemoryButton.addEventListener("click", saveMemory);
clearMemoryButton.addEventListener("click", () => {
    if (!confirm("Are you sure you want to clear SARA Memory?")) return;
    memoryInput.value = "";
    userMemory = "";
    try { localStorage.removeItem(MEMORY_KEY); } catch (error) { console.warn(error); }
    memoryDialog.close();
    showToast("SARA Memory cleared.");
});

function learnExplicitMemory(message) {
    const match = message.match(/^\s*(?:please\s+)?remember(?:\s+that)?\s+(.+?)\s*$/i);
    if (!match) return;

    const fact = match[1].trim().replace(/[.!?]+$/, "");
    if (!fact) return;

    const lines = userMemory.split("\n").map(line => line.trim()).filter(Boolean);
    if (lines.some(line => line.toLowerCase() === fact.toLowerCase())) return;

    lines.push(fact);
    userMemory = lines.join("\n").slice(0, 5000);
    try {
        localStorage.setItem(MEMORY_KEY, userMemory);
        showToast("Saved to SARA Memory.");
    } catch (error) {
        console.warn("Could not store learned memory:", error);
        showToast("Could not save memory in this browser.");
    }
}

function persistChats() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(savedChats.slice(0, MAX_SAVED_CHATS)));
        return true;
    } catch (error) {
        console.error("Could not save chats:", error);
        showToast("Browser storage is full. Delete some old chats.");
        return false;
    }
}

function saveCurrentChat() {
    if (!conversationHistory.length) return;
    const firstUserMessage = conversationHistory.find(m => m.role === "user");
    if (!firstUserMessage) return;

    const existingIndex = savedChats.findIndex(c => c.id === currentChatId);
    const existing = existingIndex >= 0 ? savedChats[existingIndex] : {};
    const chatData = {
        id: currentChatId,
        title: firstUserMessage.content.replace(/\s+/g, " ").slice(0, 32) || "New chat",
        updatedAt: Date.now(),
        createdAt: existing.createdAt || Date.now(),
        messages: conversationHistory
    };

    if (existingIndex >= 0) savedChats.splice(existingIndex, 1);
    savedChats.unshift(chatData);
    savedChats = savedChats.slice(0, MAX_SAVED_CHATS);
    persistChats();
    displayChatHistory();
}

function displayChatHistory() {
    historyContainer.replaceChildren();
    if (!savedChats.length) {
        const empty = document.createElement("p");
        empty.className = "empty-history";
        empty.textContent = "No chats yet";
        historyContainer.appendChild(empty);
        return;
    }

    savedChats.forEach(savedChat => {
        const item = document.createElement("div");
        item.className = "history-item" + (savedChat.id === currentChatId ? " active" : "");

        const title = document.createElement("button");
        title.className = "history-title";
        title.type = "button";
        title.textContent = savedChat.title || "Untitled chat";
        title.title = savedChat.title || "Open chat";
        title.addEventListener("click", () => openChat(savedChat.id));

        const remove = document.createElement("button");
        remove.className = "delete-chat";
        remove.type = "button";
        remove.textContent = "×";
        remove.title = "Delete chat";
        remove.setAttribute("aria-label", "Delete chat");
        remove.addEventListener("click", () => deleteChat(savedChat.id));

        item.append(title, remove);
        historyContainer.appendChild(item);
    });
}

function openChat(id) {
    if (isSending) return;
    const selected = savedChats.find(c => c.id === id);
    if (!selected) return;

    currentChatId = selected.id;
    conversationHistory = selected.messages.map(m => ({...m}));
    chat.replaceChildren();
    conversationHistory.forEach(m => addMessage(m.content, m.role === "user" ? "user" : "bot", m.timestamp, false));
    displayChatHistory();
    scrollToBottom();
    input.focus();
}

function deleteChat(id) {
    savedChats = savedChats.filter(c => c.id !== id);
    persistChats();
    if (currentChatId === id) startNewChat();
    else displayChatHistory();
}

clearHistoryButton.addEventListener("click", () => {
    if (!savedChats.length) return;
    if (!confirm("Delete all saved chat history from this browser?")) return;
    savedChats = [];
    try { localStorage.removeItem(STORAGE_KEY); } catch (error) { console.warn(error); }
    startNewChat();
});

function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2600);
}

function formatTime(timestamp) {
    return new Intl.DateTimeFormat([], { hour: "numeric", minute: "2-digit" }).format(new Date(timestamp || Date.now()));
}

function addMessage(text, sender, timestamp = Date.now(), withCopy = true) {
    const row = document.createElement("div");
    row.className = `message-row ${sender === "user" ? "user-row" : "bot-row"}`;

    const bubble = document.createElement("div");
    bubble.className = `message ${sender}`;
    bubble.textContent = text;

    const meta = document.createElement("div");
    meta.className = "message-meta";
    const time = document.createElement("span");
    time.textContent = formatTime(timestamp);
    meta.appendChild(time);

    if (sender === "bot" && withCopy) {
        const copy = document.createElement("button");
        copy.className = "copy-button";
        copy.type = "button";
        copy.textContent = "Copy";
        copy.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(bubble.textContent);
                copy.textContent = "Copied!";
            } catch (error) {
                const range = document.createRange();
                range.selectNodeContents(bubble);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                copy.textContent = "Select and copy";
            }
            setTimeout(() => copy.textContent = "Copy", 1600);
        });
        meta.appendChild(copy);
    }

    const content = document.createElement("div");
    content.className = "message-content";
    content.append(bubble, meta);
    row.appendChild(content);
    chat.appendChild(row);
    scrollToBottom();
    return bubble;
}

function showWelcomeScreen() {
    chat.innerHTML = `
        <div class="welcome">
            <div class="center-logo">
                <svg viewBox="0 0 100 100">
                    <path d="M17 37 C25 12 72 9 83 28 C94 47 66 53 48 57 C29 61 10 69 19 84 C29 101 72 91 84 70"/>
                    <path d="M12 50 C21 27 39 19 57 20"/>
                    <path d="M88 50 C79 73 61 81 43 80"/>
                </svg>
            </div>
            <h1>What can I help you with?</h1>
            <p>Ask anything. Explore everything.</p>
            <div class="suggestions">
                <button type="button" class="suggestion">Explain a difficult topic</button>
                <button type="button" class="suggestion">Help me write something</button>
                <button type="button" class="suggestion">Give me project ideas</button>
            </div>
        </div>`;
    document.querySelectorAll(".suggestion").forEach(button => {
        button.addEventListener("click", () => {
            input.value = button.textContent;
            input.focus();
            autoResizeInput();
        });
    });
}

function startNewChat() {
    if (isSending) return;
    conversationHistory = [];
    currentChatId = createChatId();
    input.value = "";
    input.disabled = false;
    sendButton.disabled = false;
    showWelcomeScreen();
    displayChatHistory();
    input.focus();
}

newChatButton.addEventListener("click", () => {
    if (isSending) return;
    saveCurrentChat();
    startNewChat();
});

function scrollToBottom() {
    chat.scrollTop = chat.scrollHeight;
}

function autoResizeInput() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 150) + "px";
}

input.addEventListener("input", autoResizeInput);

function setBusy(busy) {
    isSending = busy;
    input.disabled = busy;
    sendButton.disabled = busy;
    newChatButton.disabled = busy;
    sendButton.textContent = busy ? "…" : "➤";
}

async function sendMessage(message) {
    if (!message || isSending) return;

    learnExplicitMemory(message);
    const previousHistory = conversationHistory.slice();
    const userTimestamp = Date.now();

    const welcome = chat.querySelector(".welcome");
    if (welcome) welcome.remove();

    addMessage(message, "user", userTimestamp, false);
    input.value = "";
    autoResizeInput();
    setBusy(true);

    const loading = addMessage("SARA is thinking", "bot", Date.now(), false);
    loading.classList.add("typing");

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message,
                history: previousHistory,
                memory: userMemory
            })
        });

        let data;
        try { data = await response.json(); }
        catch { throw new Error("The server returned an invalid response. Check that Flask is running."); }

        if (!response.ok) throw new Error(data.reply || `Request failed (${response.status})`);

        const reply = data.reply || "I couldn't generate a response. Please try again.";
        loading.textContent = reply;
        loading.classList.remove("typing");

        conversationHistory.push(
            { role: "user", content: message, timestamp: userTimestamp },
            { role: "model", content: reply, timestamp: Date.now() }
        );
        saveCurrentChat();
    } catch (error) {
        loading.textContent = error.message || "Something went wrong. Please try again.";
        loading.classList.remove("typing");
        loading.classList.add("error-message");
        const retry = document.createElement("button");
        retry.className = "retry-button";
        retry.type = "button";
        retry.textContent = "Retry";
        retry.addEventListener("click", () => {
            loading.closest(".message-row").remove();
            sendMessage(message);
        });
        loading.parentElement.appendChild(retry);
        console.error("SARA request error:", error);
    } finally {
        setBusy(false);
        input.focus();
        scrollToBottom();
    }
}

form.addEventListener("submit", event => {
    event.preventDefault();
    sendMessage(input.value.trim());
});

input.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
    }
});

displayChatHistory();
showWelcomeScreen();
