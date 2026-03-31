module.exports = {

"[project]/.next-internal/server/app/api/chat/route/actions.js [app-rsc] (server actions loader, ecmascript)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
}}),
"[externals]/next/dist/compiled/next-server/app-route.runtime.dev.js [external] (next/dist/compiled/next-server/app-route.runtime.dev.js, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route.runtime.dev.js"));

module.exports = mod;
}}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}}),
"[externals]/next/dist/compiled/next-server/app-page.runtime.dev.js [external] (next/dist/compiled/next-server/app-page.runtime.dev.js, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page.runtime.dev.js"));

module.exports = mod;
}}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}}),
"[project]/src/lib/llm.ts [app-route] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname } = __turbopack_context__;
{
__turbopack_context__.s({
    "callLlm": (()=>callLlm),
    "detectProvider": (()=>detectProvider)
});
function detectProvider() {
    if (process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY) return "gemini";
    if (process.env.AZURE_OPENAI_API_KEY) return "azure";
    if (process.env.OPENAI_API_KEY) return "openai";
    return "none";
}
async function callLlm(req) {
    const provider = detectProvider();
    if (provider === "gemini") return callGemini(req);
    if (provider === "azure") return callAzure(req);
    if (provider === "openai") return callOpenAi(req);
    return "⚠️ No LLM provider configured. Add GEMINI_API_KEY, OPENAI_API_KEY, or Azure credentials to .env and restart.";
}
async function callGemini(req) {
    const apiKey = process.env.GEMINI_API_KEY ?? process.env.GOOGLE_API_KEY;
    const model = process.env.GEMINI_MODEL ?? "gemini-2.5-flash";
    const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
    const contents = req.messages.map((m)=>({
            role: m.role === "assistant" ? "model" : "user",
            parts: [
                {
                    text: m.content
                }
            ]
        }));
    const body = {
        contents
    };
    if (req.system) {
        body.systemInstruction = {
            parts: [
                {
                    text: req.system
                }
            ]
        };
    }
    const res = await fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`Gemini error ${res.status}: ${await res.text()}`);
    const data = await res.json();
    return data.candidates?.[0]?.content?.parts?.[0]?.text ?? "(no response)";
}
async function callAzure(req) {
    const key = process.env.AZURE_OPENAI_API_KEY;
    const endpoint = process.env.AZURE_OPENAI_ENDPOINT;
    const deployment = process.env.AZURE_OPENAI_DEPLOYMENT;
    const url = `${endpoint}/openai/deployments/${deployment}/chat/completions?api-version=2024-02-01`;
    const messages = req.system ? [
        {
            role: "system",
            content: req.system
        },
        ...req.messages
    ] : req.messages;
    const res = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "api-key": key
        },
        body: JSON.stringify({
            messages,
            max_tokens: req.max_tokens ?? 2048
        })
    });
    if (!res.ok) throw new Error(`Azure error ${res.status}: ${await res.text()}`);
    const data = await res.json();
    return data.choices?.[0]?.message?.content ?? "(no response)";
}
async function callOpenAi(req) {
    const key = process.env.OPENAI_API_KEY;
    const model = process.env.OPENAI_MODEL ?? "gpt-4o-mini";
    const messages = req.system ? [
        {
            role: "system",
            content: req.system
        },
        ...req.messages
    ] : req.messages;
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${key}`
        },
        body: JSON.stringify({
            model,
            messages,
            max_tokens: req.max_tokens ?? 2048
        })
    });
    if (!res.ok) throw new Error(`OpenAI error ${res.status}: ${await res.text()}`);
    const data = await res.json();
    return data.choices?.[0]?.message?.content ?? "(no response)";
}
}}),
"[project]/src/app/api/chat/route.ts [app-route] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname } = __turbopack_context__;
{
__turbopack_context__.s({
    "GET": (()=>GET),
    "POST": (()=>POST)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$llm$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/llm.ts [app-route] (ecmascript)");
;
;
const SYSTEM_PROMPT = `You are the ActionReady Studio assistant — an expert in analytics strategy, KPI frameworks, and use case design.

Your role is to help users design Golden Thread use cases: linking business strategy to KPIs, influencing levers, and prescriptive action codes.

Key principles:
- The Golden Thread: Strategy → KPI (North Star) → Influencing KPIs → Action Codes
- The 3-30-300 rule: 3s (status), 30s (diagnosis), 300s (action)
- Every KPI must be causal, not just correlated
- Action Codes must be imperative and prescriptive (e.g. "Review top 10 customers by DSO > 45 days")
- Keep things lean: one strategic KPI per use case, 3-6 influencing KPIs

When suggesting KPI IDs, use the dot-notation format: domain.entity.metric (e.g. wc.dso.days, sales.net_sales.amount).
When suggesting action code IDs, use the format: Domain-Type#.# (e.g. F-C1.1, C-M2.1).

If the user provides source documents, ground your suggestions in those documents.`;
async function POST(req) {
    try {
        const { messages, sources } = await req.json();
        // Build context from active sources
        const sourceContext = sources && sources.length > 0 ? "\n\n---\nSOURCE DOCUMENTS:\n" + sources.filter((s)=>s.include_in_chat).map((s)=>`[${s.name}]\n${s.content.slice(0, 4000)}`).join("\n\n---\n") : "";
        const systemWithContext = sourceContext ? SYSTEM_PROMPT + sourceContext : SYSTEM_PROMPT;
        const reply = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$llm$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["callLlm"])({
            messages,
            system: systemWithContext,
            max_tokens: 2048
        });
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            reply,
            provider: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$llm$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["detectProvider"])()
        });
    } catch (e) {
        const msg = e instanceof Error ? e.message : "Unknown error";
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            error: msg
        }, {
            status: 500
        });
    }
}
async function GET() {
    return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
        provider: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$llm$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["detectProvider"])()
    });
}
}}),

};

//# sourceMappingURL=%5Broot%20of%20the%20server%5D__adf16bb6._.js.map