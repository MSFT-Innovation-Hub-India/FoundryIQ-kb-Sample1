const form = document.getElementById("question-form");
const input = document.getElementById("question");
const askButton = document.getElementById("ask-button");
const conversation = document.getElementById("conversation");
const emptyState = document.getElementById("empty-state");
const modal = document.getElementById("citation-modal");
const modalClose = document.getElementById("close-modal");
const modalBody = document.getElementById("citation-body");

const kbConfigElement = document.getElementById("kb-config");
let kbConfig = {};
try {
    kbConfig = JSON.parse(kbConfigElement?.textContent || "{}");
} catch (error) {
    console.error("Unable to parse KB configuration", error);
}

const state = {
    interactions: [],
    config: kbConfig,
};

let markdownConfigured = false;
const configureMarkdown = () => {
    if (typeof window === "undefined" || typeof window.marked === "undefined" || markdownConfigured) {
        return;
    }

    window.marked.setOptions({
        gfm: true,
        breaks: true,
        mangle: false,
        headerIds: false,
    });
    markdownConfigured = true;
};

const escapeHtml = (unsafe = "") =>
    unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

const renderMarkdown = (text) => {
    if (!text) {
        return "";
    }

    if (typeof window !== "undefined" && window.marked && window.DOMPurify) {
        configureMarkdown();
        const rawHtml = window.marked.parse(text);
        return window.DOMPurify.sanitize(rawHtml);
    }

    return escapeHtml(text).replace(/\n/g, "<br />");
};

const formatSeconds = (value) => `${value.toFixed(3)}s`;

const toggleLoading = (isLoading) => {
    askButton.disabled = isLoading;
    if (isLoading) {
        askButton.dataset.originalText = askButton.textContent;
        askButton.textContent = "Thinking";
    } else if (askButton.dataset.originalText) {
        askButton.textContent = askButton.dataset.originalText;
    }
};

const renderConversation = () => {
    conversation.innerHTML = "";

    if (!state.interactions.length) {
        emptyState.style.display = "block";
        conversation.appendChild(emptyState);
        return;
    }

    emptyState.style.display = "none";
    state.interactions.forEach((interaction) => {
        const card = document.createElement("article");
        card.className = "message-card";

        const header = document.createElement("div");
        header.innerHTML = `<h3>Question</h3><p>${interaction.question}</p>`;

        const answerBlock = document.createElement("div");
        const renderedAnswers = interaction.answers
            .map((text) => `<div>${renderMarkdown(text)}</div>`)
            .join('<hr class="answer-divider" />');
        answerBlock.innerHTML = `<h3>Answer</h3><div class="answer-body">${renderedAnswers}</div>`;

        const citationHeading = document.createElement("h3");
        citationHeading.textContent = "Citations";
        card.appendChild(citationHeading);

        if (interaction.citations.length) {
            const citations = document.createElement("div");
            citations.className = "citation-list";
            interaction.citations.forEach((citation) => {
                const chip = document.createElement("button");
                chip.type = "button";
                chip.className = "citation-chip";
                chip.textContent = `ref:${citation.id}`;
                chip.addEventListener("click", () => openCitation(citation));
                citations.appendChild(chip);
            });
            card.appendChild(citations);
        } else {
            const citationNote = document.createElement("p");
            citationNote.className = "citation-note";
            citationNote.textContent = "No citations were returned for this answer.";
            card.appendChild(citationNote);
        }

        const metrics = document.createElement("div");
        metrics.className = "metrics-grid";
        [
            { label: "Total", value: interaction.timing.total },
            { label: "Request Prep", value: interaction.timing.requestPreparation },
            { label: "KB Retrieval", value: interaction.timing.kbRetrieval },
            { label: "Response Processing", value: interaction.timing.responseProcessing },
        ].forEach((metric) => {
            const metricCard = document.createElement("div");
            metricCard.className = "metric-card";
            metricCard.innerHTML = `<span class="label">${metric.label}</span><span class="value">${formatSeconds(
                metric.value || 0
            )}</span>`;
            metrics.appendChild(metricCard);
        });

        card.appendChild(header);
        card.appendChild(answerBlock);
        card.appendChild(metrics);
        conversation.appendChild(card);
    });
};

const openCitation = (citation) => {
    modalBody.innerHTML = `
        <h3 id="citation-title">Reference ${citation.id}</h3>
        <p><strong>Source Type:</strong> ${citation.type}</p>
        ${citation.title ? `<p><strong>Title:</strong> ${citation.title}</p>` : ""}
        ${citation.url ? `<p><a href="${citation.url}" target="_blank" rel="noreferrer noopener">Open Source ↗</a></p>` : ""}
        ${citation.citationText ? `<pre>${citation.citationText}</pre>` : ""}
        ${citation.note ? `<p>${citation.note}</p>` : ""}
    `;
    modal.setAttribute("aria-hidden", "false");
};

const closeCitation = () => {
    modal.setAttribute("aria-hidden", "true");
    modalBody.innerHTML = "";
};

modal.addEventListener("click", (event) => {
    if (event.target === modal) {
        closeCitation();
    }
});
modalClose.addEventListener("click", closeCitation);

const showError = (message) => {
    const card = document.createElement("article");
    card.className = "message-card";
    card.innerHTML = `<h3>Error</h3><p>${message}</p>`;
    conversation.prepend(card);
};

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) {
        return;
    }

    toggleLoading(true);
    try {
        const response = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });

        if (!response.ok) {
            const errorBody = await response.json().catch(() => ({}));
            throw new Error(errorBody.detail || "Unable to process your question.");
        }

        const payload = await response.json();
        state.interactions.unshift(payload);
        renderConversation();
        form.reset();
        input.focus();
    } catch (error) {
        showError(error.message);
    } finally {
        toggleLoading(false);
    }
});

renderConversation();
