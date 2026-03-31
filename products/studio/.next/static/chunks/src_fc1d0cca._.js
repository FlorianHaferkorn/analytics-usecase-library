(globalThis.TURBOPACK = globalThis.TURBOPACK || []).push(["static/chunks/src_fc1d0cca._.js", {

"[project]/src/lib/bracket.ts [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "EMPTY_DRAFT": (()=>EMPTY_DRAFT),
    "draftToYaml": (()=>draftToYaml),
    "exportPath": (()=>exportPath),
    "validateDraft": (()=>validateDraft),
    "yamlToDraft": (()=>yamlToDraft)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$js$2d$yaml$2f$dist$2f$js$2d$yaml$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/js-yaml/dist/js-yaml.mjs [app-client] (ecmascript)");
;
const EMPTY_DRAFT = {
    schema_version: "2.0",
    id: "NEW-001",
    title: "New Use Case",
    domain: "Commercial",
    governance: {
        owner_role: "",
        steward_role: ""
    },
    orchestration: {
        strategic_kpi_id: "",
        influencing_kpi_ids: [],
        action_code_ids: [],
        supporting_kpi_ids: []
    },
    value_driver_model: {
        formula: "",
        impact_direction: "maximize",
        primary_driver: "",
        impact_logic: ""
    },
    ux_layout_rules: {
        report_structure: "2-Page-Lead",
        page_1_summary: {
            title: "Overview",
            page_type: "T1_Strategic_Overview",
            template_id: "pulse",
            component_3s: {
                kpi_id: "",
                visual_type: "kpi_card"
            },
            component_30s: []
        },
        page_2_execution: {
            title: "Execution",
            page_type: "T2_Tactical_Variance",
            template_id: "action_matrix",
            component_300s: {
                evidence_grain: "entity_month",
                evidence_columns: [],
                action_panel: true,
                payload_mode: "full"
            }
        }
    },
    documentation: {
        business_factsheet: "./Business_Factsheet.md"
    }
};
function draftToYaml(draft) {
    return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$js$2d$yaml$2f$dist$2f$js$2d$yaml$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].dump(draft, {
        lineWidth: 120,
        noRefs: true,
        quotingType: '"'
    });
}
function yamlToDraft(text) {
    const parsed = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$js$2d$yaml$2f$dist$2f$js$2d$yaml$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].load(text);
    if (!parsed || typeof parsed !== "object") throw new Error("Invalid YAML — must be a mapping");
    return parsed;
}
function validateDraft(draft) {
    const errors = [];
    const warnings = [];
    if (!draft.id || draft.id === "NEW-001") warnings.push("Set a proper use case ID (e.g. COM-001)");
    if (!draft.title) errors.push("title is required");
    if (!draft.domain) errors.push("domain is required");
    if (!draft.governance?.owner_role) errors.push("governance.owner_role is required");
    if (!draft.governance?.steward_role) errors.push("governance.steward_role is required");
    if (!draft.orchestration?.strategic_kpi_id) errors.push("orchestration.strategic_kpi_id is required");
    if (!draft.orchestration?.influencing_kpi_ids?.length) warnings.push("No influencing_kpi_ids — add at least one lever KPI");
    if (!draft.orchestration?.action_code_ids?.length) warnings.push("No action_code_ids — add at least one action code");
    if (!draft.value_driver_model?.formula) warnings.push("value_driver_model.formula is empty");
    if (![
        "maximize",
        "minimize"
    ].includes(draft.value_driver_model?.impact_direction ?? "")) errors.push('impact_direction must be "maximize" or "minimize"');
    return {
        valid: errors.length === 0,
        errors,
        warnings
    };
}
function exportPath(draft) {
    const slug = draft.title.replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_|_$/g, "");
    return `core/usecases/core/${draft.id}_${slug}/UseCase_Bracket.yaml`;
}
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/store/studio.ts [app-client] (ecmascript) <locals>": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "useStudio": (()=>useStudio)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$zustand$2f$esm$2f$react$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/zustand/esm/react.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/bracket.ts [app-client] (ecmascript)");
"use client";
;
;
;
const useStudio = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$zustand$2f$esm$2f$react$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["create"])((set, get)=>({
        registry: null,
        registryLoading: false,
        registryError: null,
        setRegistry: (r)=>set({
                registry: r
            }),
        setRegistryLoading: (v)=>set({
                registryLoading: v
            }),
        setRegistryError: (e)=>set({
                registryError: e
            }),
        draft: __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["EMPTY_DRAFT"],
        yamlText: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["draftToYaml"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["EMPTY_DRAFT"]),
        setDraft: (d)=>set({
                draft: d
            }),
        setYamlText: (t)=>set({
                yamlText: t
            }),
        syncYamlFromDraft: ()=>set((s)=>({
                    yamlText: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["draftToYaml"])(s.draft)
                })),
        syncDraftFromYaml: ()=>{
            try {
                const d = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["yamlToDraft"])(get().yamlText);
                set({
                    draft: d
                });
                return null;
            } catch (e) {
                return e instanceof Error ? e.message : "Parse error";
            }
        },
        sources: [],
        addSource: (s)=>set((st)=>({
                    sources: [
                        ...st.sources,
                        s
                    ]
                })),
        removeSource: (id)=>set((st)=>({
                    sources: st.sources.filter((s)=>s.id !== id)
                })),
        toggleSource: (id)=>set((st)=>({
                    sources: st.sources.map((s)=>s.id === id ? {
                            ...s,
                            include_in_chat: !s.include_in_chat
                        } : s)
                })),
        updateSourceContent: (id, content)=>set((st)=>({
                    sources: st.sources.map((s)=>s.id === id ? {
                            ...s,
                            content
                        } : s)
                })),
        messages: [],
        chatLoading: false,
        addMessage: (m)=>set((st)=>({
                    messages: [
                        ...st.messages,
                        m
                    ]
                })),
        setChatLoading: (v)=>set({
                chatLoading: v
            }),
        clearChat: ()=>set({
                messages: []
            }),
        activeTab: "tree",
        setActiveTab: (t)=>set({
                activeTab: t
            })
    }));
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/store/studio.ts [app-client] (ecmascript) <module evaluation>": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname } = __turbopack_context__;
{
__turbopack_context__.s({});
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/bracket.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <locals>");
}}),
"[project]/src/components/ui/Button.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "Button": (()=>Button)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
;
const variants = {
    primary: "bg-brand-mint text-brand-petrol hover:bg-nagarro-green-300 disabled:opacity-50",
    secondary: "bg-theme text-theme border border-theme hover:bg-theme-tertiary disabled:opacity-50",
    ghost: "text-theme-secondary hover:bg-theme-tertiary disabled:opacity-50",
    danger: "bg-nagarro-pink-400 text-white hover:bg-nagarro-pink-500 disabled:opacity-50"
};
const sizes = {
    sm: "text-xs px-2.5 py-1.5 rounded",
    md: "text-sm px-4 py-2 rounded-md",
    lg: "text-base px-6 py-3 rounded-lg"
};
function Button({ variant = "primary", size = "md", loading, children, className = "", disabled, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
        className: `inline-flex items-center gap-2 font-medium transition-colors cursor-pointer
        ${variants[variant]} ${sizes[size]} ${className}`,
        disabled: disabled ?? loading,
        ...props,
        children: [
            loading && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: "animate-spin h-3.5 w-3.5",
                fill: "none",
                viewBox: "0 0 24 24",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("circle", {
                        className: "opacity-25",
                        cx: "12",
                        cy: "12",
                        r: "10",
                        stroke: "currentColor",
                        strokeWidth: "4"
                    }, void 0, false, {
                        fileName: "[project]/src/components/ui/Button.tsx",
                        lineNumber: 41,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                        className: "opacity-75",
                        fill: "currentColor",
                        d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    }, void 0, false, {
                        fileName: "[project]/src/components/ui/Button.tsx",
                        lineNumber: 42,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/ui/Button.tsx",
                lineNumber: 40,
                columnNumber: 9
            }, this),
            children
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/ui/Button.tsx",
        lineNumber: 33,
        columnNumber: 5
    }, this);
}
_c = Button;
var _c;
__turbopack_context__.k.register(_c, "Button");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/components/studio/SourcesPane.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "SourcesPane": (()=>SourcesPane)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$module__evaluation$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <module evaluation>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$Button$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/ui/Button.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
let _srcCounter = 0;
function nextId() {
    return `src_${++_srcCounter}`;
}
function SourcesPane() {
    _s();
    const { sources, addSource, removeSource, toggleSource } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["useStudio"])();
    const [urlInput, setUrlInput] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [textInput, setTextInput] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [textName, setTextName] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [fetching, setFetching] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [mode, setMode] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("url");
    const fileRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    async function handleAddUrl() {
        if (!urlInput.trim()) return;
        setFetching(true);
        try {
            const res = await fetch(`/api/fetch-url?url=${encodeURIComponent(urlInput)}`);
            const { text, title } = res.ok ? await res.json() : {
                text: "",
                title: urlInput
            };
            const src = {
                id: nextId(),
                type: "url",
                name: title || urlInput,
                content: text || `[Could not fetch content from ${urlInput}]`,
                include_in_chat: true
            };
            addSource(src);
            setUrlInput("");
        } finally{
            setFetching(false);
        }
    }
    function handleAddText() {
        if (!textInput.trim()) return;
        const src = {
            id: nextId(),
            type: "text",
            name: textName || `Snippet ${sources.length + 1}`,
            content: textInput,
            include_in_chat: true
        };
        addSource(src);
        setTextInput("");
        setTextName("");
    }
    async function handleFileUpload(e) {
        const files = e.target.files;
        if (!files) return;
        for (const file of Array.from(files)){
            try {
                const text = await file.text();
                const src = {
                    id: nextId(),
                    type: "text",
                    name: file.name,
                    content: text.slice(0, 50000),
                    include_in_chat: true
                };
                addSource(src);
            } catch  {
                const src = {
                    id: nextId(),
                    type: "text",
                    name: file.name,
                    content: `[Could not read file: ${file.name}]`,
                    include_in_chat: false
                };
                addSource(src);
            }
        }
        if (fileRef.current) fileRef.current.value = "";
    }
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex flex-col h-full",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "px-3 py-2 border-b border-theme shrink-0",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                        className: "text-xs font-semibold text-theme-tertiary uppercase tracking-wider",
                        children: "Sources"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/SourcesPane.tsx",
                        lineNumber: 84,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "text-[10px] text-theme-tertiary mt-0.5",
                        children: "Ground the chat with documents or URLs"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/SourcesPane.tsx",
                        lineNumber: 85,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                lineNumber: 83,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "px-3 py-2 border-b border-theme shrink-0",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex gap-0.5 mb-2",
                        children: [
                            "url",
                            "text",
                            "file"
                        ].map((m)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>setMode(m),
                                className: `text-[10px] px-2 py-1 rounded cursor-pointer font-medium transition-colors
                ${mode === m ? "bg-brand-mint text-brand-petrol" : "text-theme-tertiary hover:bg-theme-tertiary"}`,
                                children: m === "url" ? "URL" : m === "text" ? "Paste" : "Upload"
                            }, m, false, {
                                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                lineNumber: 92,
                                columnNumber: 13
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/SourcesPane.tsx",
                        lineNumber: 90,
                        columnNumber: 9
                    }, this),
                    mode === "url" ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex gap-1",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                type: "url",
                                placeholder: "https://...",
                                value: urlInput,
                                onChange: (e)=>setUrlInput(e.target.value),
                                onKeyDown: (e)=>e.key === "Enter" && handleAddUrl(),
                                className: "flex-1 text-xs bg-theme-secondary border border-theme rounded px-2 py-1.5 text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint placeholder:text-theme-tertiary"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                lineNumber: 105,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$Button$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Button"], {
                                size: "sm",
                                onClick: handleAddUrl,
                                loading: fetching,
                                disabled: !urlInput.trim(),
                                children: "Add"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                lineNumber: 113,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/SourcesPane.tsx",
                        lineNumber: 104,
                        columnNumber: 11
                    }, this) : mode === "text" ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex flex-col gap-1.5",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                type: "text",
                                placeholder: "Source name...",
                                value: textName,
                                onChange: (e)=>setTextName(e.target.value),
                                className: "text-xs bg-theme-secondary border border-theme rounded px-2 py-1.5 text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint placeholder:text-theme-tertiary"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                lineNumber: 119,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("textarea", {
                                placeholder: "Paste document text...",
                                value: textInput,
                                onChange: (e)=>setTextInput(e.target.value),
                                rows: 3,
                                className: "text-xs bg-theme-secondary border border-theme rounded px-2 py-1.5 text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint resize-none placeholder:text-theme-tertiary"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                lineNumber: 126,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$Button$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Button"], {
                                size: "sm",
                                onClick: handleAddText,
                                disabled: !textInput.trim(),
                                children: "Add"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                lineNumber: 133,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/SourcesPane.tsx",
                        lineNumber: 118,
                        columnNumber: 11
                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                ref: fileRef,
                                type: "file",
                                multiple: true,
                                accept: ".txt,.md,.yaml,.yml,.json,.csv,.tsv,.xml,.html,.pdf",
                                onChange: handleFileUpload,
                                className: "hidden"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                lineNumber: 139,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>fileRef.current?.click(),
                                className: "w-full border-2 border-dashed border-theme rounded-md py-4 text-center cursor-pointer hover:border-brand-mint transition-colors",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-theme-tertiary",
                                        children: "Click to upload files"
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                        lineNumber: 151,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-[10px] text-theme-tertiary mt-1",
                                        children: ".txt .md .yaml .json .csv .xml"
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                        lineNumber: 154,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                lineNumber: 147,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/SourcesPane.tsx",
                        lineNumber: 138,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                lineNumber: 89,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex-1 overflow-y-auto px-3 py-2 space-y-1.5",
                children: [
                    sources.length === 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "text-xs text-theme-tertiary text-center mt-6",
                        children: "No sources yet"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/SourcesPane.tsx",
                        lineNumber: 165,
                        columnNumber: 11
                    }, this),
                    sources.map((src)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: `rounded border text-xs p-2 transition-colors
              ${src.include_in_chat ? "border-brand-mint/40 bg-brand-mint/5" : "border-theme bg-theme"}`,
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex items-center gap-1.5 mb-0.5",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                            type: "checkbox",
                                            checked: src.include_in_chat,
                                            onChange: ()=>toggleSource(src.id),
                                            className: "accent-brand-mint"
                                        }, void 0, false, {
                                            fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                            lineNumber: 174,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "font-medium text-theme text-[10px] truncate flex-1",
                                            title: src.name,
                                            children: src.name
                                        }, void 0, false, {
                                            fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                            lineNumber: 180,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                            onClick: ()=>removeSource(src.id),
                                            className: "text-theme-tertiary hover:text-signal-negative ml-auto shrink-0 cursor-pointer",
                                            title: "Remove",
                                            children: "×"
                                        }, void 0, false, {
                                            fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                            lineNumber: 183,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                    lineNumber: 173,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                    className: "text-theme-tertiary line-clamp-1 pl-5 text-[10px]",
                                    children: [
                                        src.content.slice(0, 80),
                                        "..."
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/components/studio/SourcesPane.tsx",
                                    lineNumber: 191,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, src.id, true, {
                            fileName: "[project]/src/components/studio/SourcesPane.tsx",
                            lineNumber: 168,
                            columnNumber: 11
                        }, this))
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/SourcesPane.tsx",
                lineNumber: 163,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/studio/SourcesPane.tsx",
        lineNumber: 82,
        columnNumber: 5
    }, this);
}
_s(SourcesPane, "cbhlVQskVWinZfXTQRn/MmlSTr4=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["useStudio"]
    ];
});
_c = SourcesPane;
var _c;
__turbopack_context__.k.register(_c, "SourcesPane");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/components/studio/ChatPane.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "ChatPane": (()=>ChatPane)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$module__evaluation$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <module evaluation>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$Button$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/ui/Button.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
function MessageBubble({ msg }) {
    const isUser = msg.role === "user";
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: `flex ${isUser ? "justify-end" : "justify-start"} mb-3`,
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: `max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap
          ${isUser ? "bg-brand-mint text-brand-petrol rounded-br-sm" : "bg-theme border border-theme text-theme rounded-bl-sm"}`,
            children: msg.content
        }, void 0, false, {
            fileName: "[project]/src/components/studio/ChatPane.tsx",
            lineNumber: 11,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/src/components/studio/ChatPane.tsx",
        lineNumber: 10,
        columnNumber: 5
    }, this);
}
_c = MessageBubble;
function ChatPane() {
    _s();
    const { messages, chatLoading, addMessage, setChatLoading, sources, draft } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["useStudio"])();
    const [input, setInput] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [provider, setProvider] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("...");
    const bottomRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "ChatPane.useEffect": ()=>{
            fetch("/api/chat").then({
                "ChatPane.useEffect": (r)=>r.json()
            }["ChatPane.useEffect"]).then({
                "ChatPane.useEffect": (d)=>setProvider(d.provider ?? "none")
            }["ChatPane.useEffect"]);
        }
    }["ChatPane.useEffect"], []);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "ChatPane.useEffect": ()=>{
            bottomRef.current?.scrollIntoView({
                behavior: "smooth"
            });
        }
    }["ChatPane.useEffect"], [
        messages,
        chatLoading
    ]);
    async function sendMessage() {
        const text = input.trim();
        if (!text || chatLoading) return;
        setInput("");
        const userMsg = {
            role: "user",
            content: text,
            timestamp: Date.now()
        };
        addMessage(userMsg);
        setChatLoading(true);
        try {
            const draftContext = draft.orchestration.strategic_kpi_id ? `\n\nCurrent use case context: "${draft.title}" (${draft.id}), strategic KPI: ${draft.orchestration.strategic_kpi_id}` : "";
            const allMessages = [
                ...messages,
                {
                    role: "user",
                    content: text + draftContext
                }
            ];
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    messages: allMessages,
                    sources: sources.filter((s)=>s.include_in_chat)
                })
            });
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            const assistantMsg = {
                role: "assistant",
                content: data.reply,
                timestamp: Date.now()
            };
            addMessage(assistantMsg);
        } catch (e) {
            const errMsg = {
                role: "assistant",
                content: `Error: ${e instanceof Error ? e.message : "Chat error"}`,
                timestamp: Date.now()
            };
            addMessage(errMsg);
        } finally{
            setChatLoading(false);
        }
    }
    const providerLabel = {
        gemini: "Gemini",
        azure: "Azure OpenAI",
        openai: "OpenAI",
        none: "No LLM configured"
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex flex-col h-full",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "px-3 py-2 border-b border-theme shrink-0 flex items-center justify-between",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                className: "text-xs font-semibold text-theme-tertiary uppercase tracking-wider",
                                children: "Discovery Chat"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/ChatPane.tsx",
                                lineNumber: 99,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-[10px] text-theme-tertiary mt-0.5",
                                children: "Ask about KPIs, use cases, and action codes"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/ChatPane.tsx",
                                lineNumber: 100,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/ChatPane.tsx",
                        lineNumber: 98,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: `text-[10px] px-2 py-0.5 rounded font-medium
            ${provider === "none" ? "bg-nagarro-pink-100 text-nagarro-pink-400 dark:bg-nagarro-pink-900/30 dark:text-nagarro-pink-300" : "bg-nagarro-green-100 text-nagarro-green-700 dark:bg-nagarro-green-900/30 dark:text-nagarro-green-300"}`,
                        children: providerLabel[provider] ?? provider
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/ChatPane.tsx",
                        lineNumber: 102,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/ChatPane.tsx",
                lineNumber: 97,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex-1 overflow-y-auto px-3 py-3",
                children: [
                    messages.length === 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-center text-xs text-theme-tertiary mt-8 space-y-1",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "font-medium text-theme-secondary",
                                children: "Start your discovery"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/ChatPane.tsx",
                                lineNumber: 116,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                children: "Try: “Suggest a use case for reducing working capital”"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/ChatPane.tsx",
                                lineNumber: 117,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                children: "Or: “What KPIs should I track for supply chain reliability?”"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/ChatPane.tsx",
                                lineNumber: 118,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/ChatPane.tsx",
                        lineNumber: 115,
                        columnNumber: 11
                    }, this),
                    messages.map((msg, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(MessageBubble, {
                            msg: msg
                        }, i, false, {
                            fileName: "[project]/src/components/studio/ChatPane.tsx",
                            lineNumber: 122,
                            columnNumber: 11
                        }, this)),
                    chatLoading && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex justify-start mb-3",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "bg-theme border border-theme rounded-lg rounded-bl-sm px-3 py-2",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex gap-1",
                                children: [
                                    0,
                                    1,
                                    2
                                ].map((i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "w-1.5 h-1.5 rounded-full bg-brand-mint animate-bounce",
                                        style: {
                                            animationDelay: `${i * 0.15}s`
                                        }
                                    }, i, false, {
                                        fileName: "[project]/src/components/studio/ChatPane.tsx",
                                        lineNumber: 129,
                                        columnNumber: 19
                                    }, this))
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/ChatPane.tsx",
                                lineNumber: 127,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/src/components/studio/ChatPane.tsx",
                            lineNumber: 126,
                            columnNumber: 13
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/ChatPane.tsx",
                        lineNumber: 125,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        ref: bottomRef
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/ChatPane.tsx",
                        lineNumber: 139,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/ChatPane.tsx",
                lineNumber: 113,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "px-3 py-2 border-t border-theme shrink-0",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex gap-2",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("textarea", {
                                value: input,
                                onChange: (e)=>setInput(e.target.value),
                                onKeyDown: (e)=>{
                                    if (e.key === "Enter" && !e.shiftKey) {
                                        e.preventDefault();
                                        sendMessage();
                                    }
                                },
                                placeholder: "Ask about use cases, KPIs, action codes...",
                                rows: 2,
                                className: "flex-1 text-sm bg-theme-secondary border border-theme rounded-md px-3 py-2 text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint resize-none placeholder:text-theme-tertiary"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/ChatPane.tsx",
                                lineNumber: 145,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$Button$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Button"], {
                                onClick: sendMessage,
                                loading: chatLoading,
                                disabled: !input.trim(),
                                children: "Send"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/ChatPane.tsx",
                                lineNumber: 158,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/ChatPane.tsx",
                        lineNumber: 144,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "text-[10px] text-theme-tertiary mt-1",
                        children: [
                            sources.filter((s)=>s.include_in_chat).length,
                            " source(s) in context"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/ChatPane.tsx",
                        lineNumber: 162,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/ChatPane.tsx",
                lineNumber: 143,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/studio/ChatPane.tsx",
        lineNumber: 95,
        columnNumber: 5
    }, this);
}
_s(ChatPane, "iDt6vxWu+QE87cbZKokFKOKewX8=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["useStudio"]
    ];
});
_c1 = ChatPane;
var _c, _c1;
__turbopack_context__.k.register(_c, "MessageBubble");
__turbopack_context__.k.register(_c1, "ChatPane");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/components/studio/LivingTree.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "LivingTree": (()=>LivingTree)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$module__evaluation$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <module evaluation>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <locals>");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
function TreeNode({ label, value, children }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "ml-4 border-l border-theme pl-3 py-0.5",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-baseline gap-1.5",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-xs text-theme-tertiary shrink-0",
                        children: label
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 16,
                        columnNumber: 9
                    }, this),
                    value && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("code", {
                        className: "text-xs font-mono font-medium text-theme-secondary",
                        children: value
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 17,
                        columnNumber: 19
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/LivingTree.tsx",
                lineNumber: 15,
                columnNumber: 7
            }, this),
            children
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/studio/LivingTree.tsx",
        lineNumber: 14,
        columnNumber: 5
    }, this);
}
_c = TreeNode;
function LivingTree() {
    _s();
    const { draft } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["useStudio"])();
    const orch = draft.orchestration;
    const vdm = draft.value_driver_model;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "p-4 overflow-y-auto h-full",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                className: "text-xs font-semibold text-theme-tertiary uppercase tracking-wider mb-3",
                children: "Golden Thread"
            }, void 0, false, {
                fileName: "[project]/src/components/studio/LivingTree.tsx",
                lineNumber: 31,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "bg-theme rounded border border-theme px-3 py-2 mb-1",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-xs text-theme-tertiary",
                        children: "Use Case"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 37,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "font-semibold text-theme text-sm",
                        children: draft.title || "\u2014"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 38,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("code", {
                        className: "text-xs text-theme-tertiary",
                        children: draft.id
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 39,
                        columnNumber: 9
                    }, this),
                    draft.domain && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "ml-2 text-xs bg-theme-tertiary text-theme-secondary px-1.5 py-0.5 rounded",
                        children: draft.domain
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 41,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/LivingTree.tsx",
                lineNumber: 36,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "ml-2",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-xs text-theme-tertiary mb-0.5 flex items-center gap-1",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "w-2 h-px bg-theme-tertiary inline-block"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/LivingTree.tsx",
                                lineNumber: 50,
                                columnNumber: 11
                            }, this),
                            "North Star KPI (3-second signal)"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 49,
                        columnNumber: 9
                    }, this),
                    orch.strategic_kpi_id ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "bg-brand-mint/10 dark:bg-brand-mint/5 border border-brand-mint/30 rounded px-3 py-2 mb-1",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("code", {
                                className: "text-sm font-mono font-semibold text-brand-mint",
                                children: orch.strategic_kpi_id
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/LivingTree.tsx",
                                lineNumber: 55,
                                columnNumber: 13
                            }, this),
                            vdm.impact_direction && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: `ml-2 text-xs font-medium ${vdm.impact_direction === "maximize" ? "text-signal-positive" : "text-signal-negative"}`,
                                children: vdm.impact_direction === "maximize" ? "maximize" : "minimize"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/LivingTree.tsx",
                                lineNumber: 59,
                                columnNumber: 15
                            }, this),
                            vdm.formula && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-xs text-brand-mint/70 font-mono mt-1 truncate",
                                title: vdm.formula,
                                children: vdm.formula
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/LivingTree.tsx",
                                lineNumber: 68,
                                columnNumber: 15
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 54,
                        columnNumber: 11
                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "bg-theme-tertiary border border-dashed border-theme rounded px-3 py-2 mb-1 text-xs text-theme-tertiary italic",
                        children: "No strategic KPI set"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 74,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-xs text-theme-tertiary mb-0.5 mt-2 flex items-center gap-1",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "w-2 h-px bg-theme-tertiary inline-block"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/LivingTree.tsx",
                                lineNumber: 81,
                                columnNumber: 11
                            }, this),
                            "Influencing KPIs (30-second levers)"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 80,
                        columnNumber: 9
                    }, this),
                    orch.influencing_kpi_ids && orch.influencing_kpi_ids.length > 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "space-y-1 ml-2",
                        children: orch.influencing_kpi_ids.map((kid)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "bg-theme border border-theme rounded px-2.5 py-1.5 flex items-center gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-theme-tertiary text-xs",
                                        children: "○"
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                                        lineNumber: 91,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("code", {
                                        className: "text-xs font-mono text-theme-secondary",
                                        children: kid
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                                        lineNumber: 92,
                                        columnNumber: 17
                                    }, this),
                                    vdm.primary_driver === kid && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "ml-auto text-[10px] bg-nagarro-yellow-100 text-nagarro-yellow-700 dark:bg-nagarro-yellow-700/20 dark:text-nagarro-yellow-300 px-1.5 py-0.5 rounded",
                                        children: "primary driver"
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                                        lineNumber: 94,
                                        columnNumber: 19
                                    }, this)
                                ]
                            }, kid, true, {
                                fileName: "[project]/src/components/studio/LivingTree.tsx",
                                lineNumber: 87,
                                columnNumber: 15
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 85,
                        columnNumber: 11
                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "ml-2 text-xs text-theme-tertiary italic",
                        children: "No influencing KPIs"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 102,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-xs text-theme-tertiary mb-0.5 mt-2 flex items-center gap-1",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "w-2 h-px bg-theme-tertiary inline-block"
                            }, void 0, false, {
                                fileName: "[project]/src/components/studio/LivingTree.tsx",
                                lineNumber: 107,
                                columnNumber: 11
                            }, this),
                            "Action Codes (300-second prescriptions)"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 106,
                        columnNumber: 9
                    }, this),
                    orch.action_code_ids && orch.action_code_ids.length > 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "space-y-1 ml-2",
                        children: orch.action_code_ids.map((aid)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "bg-nagarro-purple-300/10 dark:bg-nagarro-purple-900/20 border border-nagarro-purple-300/30 dark:border-nagarro-purple-700/30 rounded px-2.5 py-1.5 flex items-center gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-nagarro-purple-500 dark:text-nagarro-purple-300 text-xs",
                                        children: "⚡"
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                                        lineNumber: 117,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("code", {
                                        className: "text-xs font-mono text-nagarro-purple-700 dark:text-nagarro-purple-300 font-medium",
                                        children: aid
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                                        lineNumber: 118,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, aid, true, {
                                fileName: "[project]/src/components/studio/LivingTree.tsx",
                                lineNumber: 113,
                                columnNumber: 15
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 111,
                        columnNumber: 11
                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "ml-2 text-xs text-theme-tertiary italic",
                        children: "No action codes"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                        lineNumber: 123,
                        columnNumber: 11
                    }, this),
                    (draft.governance.owner_role || draft.governance.steward_role) && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-xs text-theme-tertiary mb-0.5 mt-3 flex items-center gap-1",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "w-2 h-px bg-theme-tertiary inline-block"
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                                        lineNumber: 130,
                                        columnNumber: 15
                                    }, this),
                                    "Governance"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/components/studio/LivingTree.tsx",
                                lineNumber: 129,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "ml-2 space-y-1",
                                children: [
                                    draft.governance.owner_role && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(TreeNode, {
                                        label: "Business Owner",
                                        value: draft.governance.owner_role
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                                        lineNumber: 135,
                                        columnNumber: 17
                                    }, this),
                                    draft.governance.steward_role && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(TreeNode, {
                                        label: "Data Steward",
                                        value: draft.governance.steward_role
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/studio/LivingTree.tsx",
                                        lineNumber: 138,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/components/studio/LivingTree.tsx",
                                lineNumber: 133,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/LivingTree.tsx",
                lineNumber: 48,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/studio/LivingTree.tsx",
        lineNumber: 30,
        columnNumber: 5
    }, this);
}
_s(LivingTree, "SMQzG4e0HW0Hq4o8xQw422jNvRQ=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["useStudio"]
    ];
});
_c1 = LivingTree;
var _c, _c1;
__turbopack_context__.k.register(_c, "TreeNode");
__turbopack_context__.k.register(_c1, "LivingTree");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/components/studio/YamlEditor.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "YamlEditor": (()=>YamlEditor)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$module__evaluation$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <module evaluation>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/bracket.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$Button$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/ui/Button.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
;
function YamlEditor() {
    _s();
    const { yamlText, setYamlText, syncDraftFromYaml, syncYamlFromDraft, draft } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["useStudio"])();
    const [parseError, setParseError] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [exporting, setExporting] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [exportMsg, setExportMsg] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    function handleSync() {
        const err = syncDraftFromYaml();
        setParseError(err);
        if (!err) setExportMsg(null);
    }
    function handleReformat() {
        const err = syncDraftFromYaml();
        if (!err) {
            syncYamlFromDraft();
            setParseError(null);
        } else {
            setParseError(err);
        }
    }
    async function handleExport() {
        const err = syncDraftFromYaml();
        if (err) {
            setParseError(err);
            return;
        }
        const validation = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["validateDraft"])(draft);
        if (!validation.valid) {
            setExportMsg({
                ok: false,
                text: validation.errors.join(" | ")
            });
            return;
        }
        setExporting(true);
        try {
            const path = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["exportPath"])(draft);
            const res = await fetch("/api/export", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    yamlText,
                    exportPath: path
                })
            });
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            setExportMsg({
                ok: true,
                text: `Exported to ${path}`
            });
        } catch (e) {
            setExportMsg({
                ok: false,
                text: e instanceof Error ? e.message : "Export failed"
            });
        } finally{
            setExporting(false);
        }
    }
    const validation = (()=>{
        try {
            return (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$bracket$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["validateDraft"])(draft);
        } catch  {
            return {
                valid: false,
                errors: [],
                warnings: []
            };
        }
    })();
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex flex-col h-full",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "px-3 py-2 border-b border-theme shrink-0 flex items-center gap-2 flex-wrap",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$Button$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Button"], {
                        size: "sm",
                        variant: "secondary",
                        onClick: handleSync,
                        children: "Apply YAML"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/YamlEditor.tsx",
                        lineNumber: 69,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$Button$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Button"], {
                        size: "sm",
                        variant: "ghost",
                        onClick: handleReformat,
                        children: "Reformat"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/YamlEditor.tsx",
                        lineNumber: 72,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$Button$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Button"], {
                        size: "sm",
                        variant: "secondary",
                        onClick: syncYamlFromDraft,
                        children: "Refresh from tree"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/YamlEditor.tsx",
                        lineNumber: 75,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$Button$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Button"], {
                        size: "sm",
                        onClick: handleExport,
                        loading: exporting,
                        className: "ml-auto",
                        children: "Export to repo"
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/YamlEditor.tsx",
                        lineNumber: 78,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/YamlEditor.tsx",
                lineNumber: 68,
                columnNumber: 7
            }, this),
            (parseError || validation.errors.length > 0 || validation.warnings.length > 0) && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "px-3 py-2 border-b border-theme shrink-0 space-y-0.5",
                children: [
                    parseError && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "text-xs text-signal-negative",
                        children: parseError
                    }, void 0, false, {
                        fileName: "[project]/src/components/studio/YamlEditor.tsx",
                        lineNumber: 86,
                        columnNumber: 26
                    }, this),
                    validation.errors.map((e, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-xs text-signal-negative",
                            children: e
                        }, i, false, {
                            fileName: "[project]/src/components/studio/YamlEditor.tsx",
                            lineNumber: 88,
                            columnNumber: 13
                        }, this)),
                    validation.warnings.map((w, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-xs text-signal-warning",
                            children: w
                        }, i, false, {
                            fileName: "[project]/src/components/studio/YamlEditor.tsx",
                            lineNumber: 91,
                            columnNumber: 13
                        }, this))
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/studio/YamlEditor.tsx",
                lineNumber: 85,
                columnNumber: 9
            }, this),
            exportMsg && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: `px-3 py-1.5 text-xs border-b border-theme shrink-0
          ${exportMsg.ok ? "text-signal-positive" : "text-signal-negative"}`,
                children: exportMsg.text
            }, void 0, false, {
                fileName: "[project]/src/components/studio/YamlEditor.tsx",
                lineNumber: 98,
                columnNumber: 9
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("textarea", {
                value: yamlText,
                onChange: (e)=>{
                    setYamlText(e.target.value);
                    setParseError(null);
                    setExportMsg(null);
                },
                className: "flex-1 yaml-editor bg-nagarro-blue-900 dark:bg-surface-dark text-nagarro-green-300 p-4 resize-none focus:outline-none w-full",
                spellCheck: false,
                autoComplete: "off",
                autoCorrect: "off"
            }, void 0, false, {
                fileName: "[project]/src/components/studio/YamlEditor.tsx",
                lineNumber: 105,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/studio/YamlEditor.tsx",
        lineNumber: 66,
        columnNumber: 5
    }, this);
}
_s(YamlEditor, "FueQg0sT/a5d9VTElXV/wmeksd0=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["useStudio"]
    ];
});
_c = YamlEditor;
var _c;
__turbopack_context__.k.register(_c, "YamlEditor");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/studio/page.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "default": (()=>StudioPage)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$module__evaluation$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <module evaluation>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/src/store/studio.ts [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$studio$2f$SourcesPane$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/studio/SourcesPane.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$studio$2f$ChatPane$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/studio/ChatPane.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$studio$2f$LivingTree$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/studio/LivingTree.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$studio$2f$YamlEditor$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/studio/YamlEditor.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
;
;
;
function StudioPage() {
    _s();
    const { setRegistry, setRegistryLoading, setRegistryError, activeTab, setActiveTab } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["useStudio"])();
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "StudioPage.useEffect": ()=>{
            setRegistryLoading(true);
            fetch("/api/registry").then({
                "StudioPage.useEffect": (r)=>r.json()
            }["StudioPage.useEffect"]).then({
                "StudioPage.useEffect": (d)=>{
                    if (d.error) setRegistryError(d.error);
                    else setRegistry(d);
                }
            }["StudioPage.useEffect"]).catch({
                "StudioPage.useEffect": (e)=>setRegistryError(e.message)
            }["StudioPage.useEffect"]).finally({
                "StudioPage.useEffect": ()=>setRegistryLoading(false)
            }["StudioPage.useEffect"]);
        }
    }["StudioPage.useEffect"], [
        setRegistry,
        setRegistryLoading,
        setRegistryError
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "h-full flex overflow-hidden",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "w-56 shrink-0 border-r border-theme bg-theme flex flex-col overflow-hidden",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$studio$2f$SourcesPane$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["SourcesPane"], {}, void 0, false, {
                    fileName: "[project]/src/app/studio/page.tsx",
                    lineNumber: 29,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/studio/page.tsx",
                lineNumber: 28,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex-1 border-r border-theme bg-theme-secondary flex flex-col overflow-hidden min-w-0",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$studio$2f$ChatPane$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["ChatPane"], {}, void 0, false, {
                    fileName: "[project]/src/app/studio/page.tsx",
                    lineNumber: 34,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/studio/page.tsx",
                lineNumber: 33,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "w-[480px] shrink-0 bg-theme flex flex-col overflow-hidden",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "border-b border-theme flex items-center px-3 shrink-0",
                        children: [
                            "tree",
                            "yaml"
                        ].map((t)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>setActiveTab(t),
                                className: `px-4 py-2.5 text-xs font-semibold uppercase tracking-wider border-b-2 transition-colors cursor-pointer
                ${activeTab === t ? "border-brand-mint text-brand-mint" : "border-transparent text-theme-tertiary hover:text-theme-secondary"}`,
                                children: t === "tree" ? "Living Tree" : "YAML Editor"
                            }, t, false, {
                                fileName: "[project]/src/app/studio/page.tsx",
                                lineNumber: 41,
                                columnNumber: 13
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/src/app/studio/page.tsx",
                        lineNumber: 39,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex-1 overflow-hidden",
                        children: activeTab === "tree" ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$studio$2f$LivingTree$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["LivingTree"], {}, void 0, false, {
                            fileName: "[project]/src/app/studio/page.tsx",
                            lineNumber: 55,
                            columnNumber: 35
                        }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$studio$2f$YamlEditor$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["YamlEditor"], {}, void 0, false, {
                            fileName: "[project]/src/app/studio/page.tsx",
                            lineNumber: 55,
                            columnNumber: 52
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/src/app/studio/page.tsx",
                        lineNumber: 54,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/studio/page.tsx",
                lineNumber: 38,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/app/studio/page.tsx",
        lineNumber: 26,
        columnNumber: 5
    }, this);
}
_s(StudioPage, "JiERHvXCLLNNdkK3fW2wFTWIwNk=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$store$2f$studio$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["useStudio"]
    ];
});
_c = StudioPage;
var _c;
__turbopack_context__.k.register(_c, "StudioPage");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
}]);

//# sourceMappingURL=src_fc1d0cca._.js.map