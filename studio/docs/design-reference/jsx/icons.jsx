// Fake, coherent analytics-framework data
const FRAMEWORK = {
  domains: [
    { id: "revenue",    name: "Revenue",      count: 34, color: "250" },
    { id: "growth",     name: "Growth",       count: 22, color: "180" },
    { id: "product",    name: "Product",      count: 41, color: "310" },
    { id: "retention",  name: "Retention",    count: 18, color: "30"  },
    { id: "operations", name: "Operations",   count: 27, color: "140" },
  ],

  metrics: [
    { id: "mrr",              domain: "revenue",   name: "Monthly Recurring Revenue", ref: "met.revenue.mrr",            type: "Sum",    unit: "USD",  owner: "R. Okafor",     grain: "day",   status: "certified", updated: "2h ago",  deps: 4 },
    { id: "arr",              domain: "revenue",   name: "Annual Recurring Revenue",  ref: "met.revenue.arr",            type: "Sum",    unit: "USD",  owner: "R. Okafor",     grain: "day",   status: "certified", updated: "2h ago",  deps: 2 },
    { id: "nrr",              domain: "revenue",   name: "Net Revenue Retention",     ref: "met.revenue.nrr",            type: "Ratio",  unit: "%",    owner: "L. Chen",       grain: "month", status: "certified", updated: "1d ago",  deps: 5 },
    { id: "grr",              domain: "revenue",   name: "Gross Revenue Retention",   ref: "met.revenue.grr",            type: "Ratio",  unit: "%",    owner: "L. Chen",       grain: "month", status: "review",    updated: "3d ago",  deps: 3 },
    { id: "cac",              domain: "growth",    name: "Customer Acquisition Cost", ref: "met.growth.cac",             type: "Ratio",  unit: "USD",  owner: "M. Park",       grain: "week",  status: "certified", updated: "4h ago",  deps: 6 },
    { id: "ltv",              domain: "retention", name: "Customer Lifetime Value",   ref: "met.retention.ltv",          type: "Model",  unit: "USD",  owner: "M. Park",       grain: "month", status: "review",    updated: "yday",    deps: 7 },
    { id: "dau",              domain: "product",   name: "Daily Active Users",        ref: "met.product.dau",            type: "Count",  unit: "users",owner: "S. Villanueva", grain: "day",   status: "certified", updated: "12m ago", deps: 2 },
    { id: "mau",              domain: "product",   name: "Monthly Active Users",      ref: "met.product.mau",            type: "Count",  unit: "users",owner: "S. Villanueva", grain: "day",   status: "certified", updated: "12m ago", deps: 2 },
    { id: "activation_rate",  domain: "product",   name: "Activation Rate",           ref: "met.product.activation_rate",type: "Ratio",  unit: "%",    owner: "S. Villanueva", grain: "day",   status: "certified", updated: "1h ago",  deps: 4 },
    { id: "churn_logo",       domain: "retention", name: "Logo Churn",                ref: "met.retention.churn_logo",   type: "Ratio",  unit: "%",    owner: "L. Chen",       grain: "month", status: "certified", updated: "yday",    deps: 3 },
    { id: "time_to_value",    domain: "product",   name: "Time to Value",             ref: "met.product.time_to_value",  type: "Median", unit: "days", owner: "A. Haferkorn",  grain: "week",  status: "draft",     updated: "5m ago",  deps: 3 },
    { id: "ticket_volume",    domain: "operations",name: "Support Ticket Volume",     ref: "met.ops.ticket_volume",      type: "Count",  unit: "count",owner: "J. Wiremu",     grain: "day",   status: "certified", updated: "30m ago", deps: 1 },
  ],

  dimensions: [
    { id: "plan_tier",  name: "Plan Tier",         ref: "dim.plan_tier",     cardinality: 4,    source: "billing" },
    { id: "region",     name: "Region",            ref: "dim.region",        cardinality: 7,    source: "crm" },
    { id: "channel",    name: "Acquisition Channel",ref:"dim.channel",       cardinality: 12,   source: "attribution" },
    { id: "cohort",     name: "Signup Cohort",     ref: "dim.cohort",        cardinality: 48,   source: "events" },
    { id: "company_size",name:"Company Size",      ref: "dim.company_size",  cardinality: 5,    source: "crm" },
    { id: "device",     name: "Device",            ref: "dim.device",        cardinality: 3,    source: "events" },
  ],

  sources: [
    { id: "billing",     name: "Stripe Billing",      ref: "src.billing",     rows: "1.2M",  lastSync: "3m ago" },
    { id: "events",      name: "Product Events",      ref: "src.events",      rows: "412M",  lastSync: "live"   },
    { id: "crm",         name: "CRM",                 ref: "src.crm",         rows: "48k",   lastSync: "1h ago" },
    { id: "attribution", name: "Attribution Pipeline",ref: "src.attribution", rows: "9.4M",  lastSync: "12m ago"},
    { id: "support",     name: "Support Tickets",     ref: "src.support",     rows: "640k",  lastSync: "5m ago" },
  ],

  activity: [
    { who: "R. Okafor",     what: "certified",       target: "met.revenue.nrr",       when: "2h ago" },
    { who: "A. Haferkorn",  what: "drafted",         target: "met.product.time_to_value", when: "5m ago" },
    { who: "M. Park",       what: "commented on",    target: "met.retention.ltv",     when: "1h ago" },
    { who: "S. Villanueva", what: "updated SQL for", target: "met.product.activation_rate", when: "1h ago" },
    { who: "L. Chen",       what: "requested review for", target: "met.revenue.grr",  when: "3d ago" },
  ],
};

// Graph layout for canvas (hand-placed for narrative clarity)
const GRAPH = {
  nodes: [
    // sources (left column)
    { id: "src.events",      kind: "source",    x: 60,  y: 120, label: "Product Events",    sub: "412M rows · live" },
    { id: "src.billing",     kind: "source",    x: 60,  y: 260, label: "Stripe Billing",    sub: "1.2M rows · 3m"   },
    { id: "src.crm",         kind: "source",    x: 60,  y: 400, label: "CRM",               sub: "48k rows · 1h"    },
    { id: "src.attribution", kind: "source",    x: 60,  y: 540, label: "Attribution",       sub: "9.4M rows · 12m"  },

    // dimensions (col 2, small)
    { id: "dim.plan_tier",   kind: "dimension", x: 310, y: 210, label: "Plan Tier",        sub: "4 values"   },
    { id: "dim.region",      kind: "dimension", x: 310, y: 300, label: "Region",           sub: "7 values"   },
    { id: "dim.channel",     kind: "dimension", x: 310, y: 470, label: "Channel",          sub: "12 values"  },
    { id: "dim.cohort",      kind: "dimension", x: 310, y: 120, label: "Signup Cohort",    sub: "48 values"  },

    // base metrics (col 3)
    { id: "met.product.dau",             kind: "metric", x: 560, y: 120, label: "DAU",                 sub: "count · day" },
    { id: "met.product.mau",             kind: "metric", x: 560, y: 200, label: "MAU",                 sub: "count · day" },
    { id: "met.product.activation_rate", kind: "metric", x: 560, y: 290, label: "Activation Rate",     sub: "ratio · day" },
    { id: "met.revenue.mrr",             kind: "metric", x: 560, y: 380, label: "MRR",                 sub: "sum · day"   },
    { id: "met.retention.churn_logo",    kind: "metric", x: 560, y: 470, label: "Logo Churn",          sub: "ratio · mo"  },
    { id: "met.growth.cac",              kind: "metric", x: 560, y: 560, label: "CAC",                 sub: "ratio · wk"  },

    // derived (col 4)
    { id: "met.revenue.nrr",     kind: "derived",  x: 830, y: 200, label: "NRR",   sub: "derived · certified" },
    { id: "met.revenue.arr",     kind: "derived",  x: 830, y: 380, label: "ARR",   sub: "derived · certified" },
    { id: "met.retention.ltv",   kind: "derived",  x: 830, y: 510, label: "LTV",   sub: "model · review"      },

    // north star (col 5)
    { id: "goal.efficient_growth", kind: "goal", x: 1080, y: 340, label: "Efficient Growth", sub: "North Star" },
  ],
  edges: [
    ["src.events", "dim.cohort"],
    ["src.events", "met.product.dau"],
    ["src.events", "met.product.mau"],
    ["src.events", "met.product.activation_rate"],
    ["src.billing", "met.revenue.mrr"],
    ["src.billing", "dim.plan_tier"],
    ["src.crm", "dim.region"],
    ["src.crm", "met.retention.churn_logo"],
    ["src.attribution", "dim.channel"],
    ["src.attribution", "met.growth.cac"],
    ["met.revenue.mrr", "met.revenue.arr"],
    ["met.revenue.mrr", "met.revenue.nrr"],
    ["met.retention.churn_logo", "met.revenue.nrr"],
    ["met.retention.churn_logo", "met.retention.ltv"],
    ["met.revenue.mrr", "met.retention.ltv"],
    ["met.revenue.nrr", "goal.efficient_growth"],
    ["met.revenue.arr", "goal.efficient_growth"],
    ["met.growth.cac", "goal.efficient_growth"],
    ["met.retention.ltv", "goal.efficient_growth"],
  ],
};

window.FRAMEWORK = FRAMEWORK;
window.GRAPH = GRAPH;
