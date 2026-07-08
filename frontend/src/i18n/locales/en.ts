import type { Messages } from "../types";

const en: Messages = {
  // Language switcher / language names
  "language.label": "Language",
  "language.en": "English",
  "language.es": "Español",
  "language.ptBR": "Português",
  "language.fr": "Français",
  "language.de": "Deutsch",
  "language.uk": "Українська",
  "language.ru": "Русский",

  // App / nav
  "app.title": "XMR Fund Transparency Suite",
  "nav.news": "News",
  "nav.wallets": "Wallets",
  "nav.settings": "Settings",
  "nav.disconnect": "Disconnect",

  // Common
  "common.active": "Active",
  "common.inactive": "Inactive",
  "common.refresh": "Refresh",
  "common.refreshing": "Refreshing...",
  "common.loading": "Loading...",
  "common.cancel": "Cancel",
  "common.delete": "Delete",
  "common.edit": "Edit",
  "common.save": "Save",
  "common.saving": "Saving...",
  "common.creating": "Creating...",
  "common.copied": "Copied!",
  "common.failed": "Failed",
  "common.copyAddress": "Copy address",
  "common.copyEmbedCode": "Copy embed code",
  "common.copyUrl": "Copy URL",
  "common.processing": "Processing...",
  "common.retry": "Retry",
  "common.optional": "optional",
  "common.wallet": "Wallet",
  "common.fund": "Fund",
  "common.description": "Description",
  "common.confirm": "Confirm",
  "common.activate": "Activate",
  "common.deactivate": "Deactivate",
  "common.activating": "Activating...",
  "common.deactivating": "Deactivating...",
  "common.selectWallet": "Select wallet",
  "common.selectFund": "Select fund",
  "common.createFund": "Create Fund",
  "common.saveChanges": "Save Changes",
  "common.deleteFund": "Delete Fund",
  "common.failedLoadWallets": "Failed to load wallets",
  "common.failedDeleteWallet": "Failed to delete wallet",
  "common.failedCreateWallet": "Failed to create wallet",
  "common.failedUpdateFormat": "Failed to update format",

  // Login screen
  "login.connectTitle": "Connect to Dashboard",
  "login.description":
    "Enter the API key that was configured during deployment. This key authenticates all requests to the backend.",
  "login.apiKey": "API Key",
  "login.apiKeyPlaceholder": "Enter your API key...",
  "login.validating": "Validating...",
  "login.connect": "Connect",
  "login.privacyNote":
    "The API key is stored locally in your browser and never sent to third parties.",

  // Dashboard
  "dashboard.loadingData": "Loading data...",
  "dashboard.errorLoadingTitle": "Error Loading Data",
  "dashboard.noWalletTitle": "No Wallet Configured",
  "dashboard.noWalletDesc":
    "Create a wallet and fund to start tracking incoming Monero donations.",
  "dashboard.goToWallets": "Go to Wallets",
  "dashboard.noFundTitle": "No Fund Configured",
  "dashboard.noFundDesc":
    "This wallet has no funds yet. Create a fund to start tracking donations.",
  "dashboard.loadingWallet": "Loading wallet data...",

  // Fund card
  "fundcard.scanError": "Scan Error",
  "fundcard.scanning": "Scanning",
  "fundcard.totalReceived": "Total Received",
  "fundcard.target": "Target",
  "fundcard.transactions": "Transactions",
  "fundcard.lastScan": "Last Scan",
  "fundcard.never": "Never",
  "fundcard.blockHeight": "Block height:",
  "fundcard.notStarted": "Not started",
  "fundcard.scanErrorTitle": "Scan error",

  // Transaction table
  "txtable.title": "Recent Transactions",
  "txtable.collapse": "Collapse",
  "txtable.showAll": "Show all ({count})",
  "txtable.colDate": "Date",
  "txtable.colAmount": "Amount",
  "txtable.colConfirmations": "Confirmations",
  "txtable.colHeight": "Height",
  "txtable.colTxid": "TXID",
  "txtable.noMatch": "No transactions match the current filters.",

  // Filters
  "filters.title": "Filters & Sorting",
  "filters.reset": "Reset Filters",
  "filters.startDate": "Start Date",
  "filters.endDate": "End Date",
  "filters.amountTier": "Amount Tier",
  "filters.sortBy": "Sort By",
  "filters.addSort": "Add Sort",
  "filters.noSorting":
    "No sorting applied (default: block height descending)",
  "filters.descending": "Descending",
  "filters.ascending": "Ascending",

  // Tiers
  "tier.micro": "Micro",
  "tier.medium": "Medium",
  "tier.large": "Large",
  "tier.whale": "Whale",
  "tierDesc.micro": "< 0.1 XMR",
  "tierDesc.medium": "0.1 — 1.0 XMR",
  "tierDesc.large": "1.0 — 5.0 XMR",
  "tierDesc.whale": "> 5.0 XMR",

  // Sort fields
  "sortField.timestamp": "Date",
  "sortField.amount_xmr": "Amount",
  "sortField.confirmations": "Confirmations",

  // Charts
  "charts.cumulativeReceived": "Cumulative Received XMR",
  "charts.linear": "Linear",
  "charts.log": "Log",
  "charts.noData": "No transaction data available yet",
  "charts.donationSize": "Donation Size Segmentation",
  "charts.goalProgress": "Goal & Progress",
  "charts.bar": "Bar",
  "charts.gauge": "Gauge",
  "charts.noTargetConfigured":
    "No target funding goal is currently configured for this fund. You can set one up in",
  "charts.noTargetSettingsLink": "Settings",
  "charts.noTargetSuffix": ".",
  "charts.volumeDistribution": "XMR Volume Distribution",
  "charts.received": "Received",
  "charts.remaining": "Remaining",
  "charts.cumulativeXmr": "Cumulative XMR",
  "charts.target": "Target",
  "charts.xmrVolume": "XMR Volume",
  "charts.donations": {
    one: "{count} donation",
    other: "{count} donations",
  },

  // Wallets page
  "wallets.title": "Wallets",
  "wallets.subtitle":
    "Manage your view-only wallets. Each wallet can have multiple funds with their own deposit addresses.",
  "wallets.createWallet": "Create Wallet",
  "wallets.loadingWallets": "Loading wallets...",
  "wallets.errorLoadingTitle": "Error Loading Wallets",
  "wallets.setUpWallet": "Set Up Your Wallet",
  "wallets.createNew": "Create New Wallet",
  "wallets.createDesc":
    "Connect a Monero view-only wallet by providing its primary address and private view key. This information is encrypted before storage.",
  "wallets.walletName": "Wallet Name",
  "wallets.walletNamePh": "My Monero Wallet",
  "wallets.walletNameHint": "A display name for this wallet.",
  "wallets.primaryAddress": "Primary Address",
  "wallets.primaryAddressHint":
    "Your wallet's primary Monero address (95 characters, starts with 4/8/A/B).",
  "wallets.viewKey": "Private View Key",
  "wallets.viewKeyPh": "64 hex characters",
  "wallets.viewKeyHint": "Your wallet's private view key (64 hex characters).",
  "wallets.neverShareSpend": "Never share your spend key.",
  "wallets.startHeight": "Start Height",
  "wallets.startHeightHint":
    "Block height to start scanning from. Lower = more history, higher = faster sync.",
  "wallets.created": "Created",
  "wallets.lastScannedHeight": "Last Scanned Height",
  "wallets.lastScanAt": "Last Scan At",
  "wallets.scanError": "Scan error",
  "wallets.settingsFunds": "Settings & Funds",
  "wallets.confirmDeleteTitle": "Confirm Deletion",
  "wallets.confirmDeleteMsg":
    "Are you sure you want to delete the wallet {name}?",
  "wallets.deleteWallet": "Delete Wallet",
  "wallets.deleting": "Deleting...",
  "wallets.deleteWarning":
    "All associated funds, transactions, and posts will be permanently removed. This cannot be undone.",

  // Wallet detail
  "walletdetail.loading": "Loading wallet...",
  "walletdetail.errorTitle": "Error Loading Wallet",
  "walletdetail.notFoundTitle": "Wallet Not Found",
  "walletdetail.notFoundDesc":
    "The wallet you are looking for does not exist or has been removed.",
  "walletdetail.backToWallets": "Back to Wallets",
  "walletdetail.walletSettings": "Wallet Settings",
  "walletdetail.funds": "Funds",
  "walletdetail.colNumber": "#",
  "walletdetail.colLabel": "Label",
  "walletdetail.colTarget": "Target",
  "walletdetail.colReceived": "Received",
  "walletdetail.colStatus": "Status",
  "walletdetail.colActions": "Actions",
  "walletdetail.manage": "Manage",
  "walletdetail.noFunds": "No funds yet. Create one to get started.",
  "walletdetail.loadingFunds": "Loading funds...",
  "walletdetail.deactivateWallet": "Deactivate Wallet",
  "walletdetail.activateWallet": "Activate Wallet",
  "walletdetail.deactivateMsg":
    "Are you sure you want to deactivate this wallet? The scanner will stop processing this wallet.",
  "walletdetail.activateMsg":
    "Are you sure you want to activate this wallet? The scanner will resume processing.",

  // Fund detail
  "funddetail.loading": "Loading fund data...",
  "funddetail.errorTitle": "Error Loading Fund",
  "funddetail.notFoundTitle": "Fund Not Found",
  "funddetail.notFoundDesc":
    "The fund you are looking for does not exist or you don't have access.",
  "funddetail.backToWallets": "Back to Wallets",
  "funddetail.fundSettings": "Fund Settings",
  "funddetail.widgetPreview": "Widget Preview & Embed",
  "funddetail.printPng": "Print to PNG",
  "funddetail.businessCard": "Business Card",
  "funddetail.wide": "Wide",
  "funddetail.vertical": "Vertical",
  "funddetail.widgetDesc":
    "This widget shows your fund publicly. Anyone with the link can view it.",
  "funddetail.loadingWidget": "Loading widget data...",
  "funddetail.updated": "Updated:",
  "funddetail.copyAddress": "Copy Address",
  "funddetail.poweredBy": "Widget powered by xmrfts.com",
  "funddetail.news": "News",
  "funddetail.loadingNews": "Loading...",
  "funddetail.failedNews": "Failed to load news",
  "funddetail.noNews": "No news yet",
  "funddetail.loadMore": "Load more",
  "funddetail.embedCode": "Embed Code",
  "funddetail.widgetJsonUrl": "Widget JSON URL",
  "funddetail.widgetCacheNote":
    "The widget is cached for 60 seconds and rate-limited to 60 requests per minute per IP.",
  "funddetail.deleteTitle": "Delete Fund",
  "funddetail.deleteSubtitle": "This action cannot be undone.",
  "funddetail.deleteMsg":
    "Are you sure you want to delete {label}? All associated transactions and posts will be permanently removed.",
  "funddetail.deactivateFund": "Deactivate Fund",
  "funddetail.activateFund": "Activate Fund",
  "funddetail.deactivateSubtitle": "This will stop tracking new transactions.",
  "funddetail.activateSubtitle":
    "This will resume tracking new transactions.",
  "funddetail.deactivateMsg":
    "Are you sure you want to deactivate this fund? It will no longer appear in public widgets or receive scan updates.",
  "funddetail.activateMsg":
    "Are you sure you want to activate this fund? It will resume appearing in public widgets and receiving scan updates.",
  "funddetail.depositAddressHint":
    "Changing the deposit address will trigger a full rescan of the blockchain.",
  "funddetail.websiteHint": "Enter without https:// — e.g. example.com",

  // Fund form fields
  "fund.label": "Label",
  "fund.labelPh": "Campaign name",
  "fund.labelPh2": "My Fundraiser",
  "fund.descriptionPh": "What is this fund for?",
  "fund.descriptionPh2": "Describe the purpose of this fund...",
  "fund.depositAddress": "Deposit Address",
  "fund.depositAddressPh": "4...",
  "fund.depositAddressPh2": "86erTZz...",
  "fund.targetAmount": "Target Amount (XMR)",
  "fund.targetAmountPh": "0.00",
  "fund.targetAmountPh2": "e.g. 100.00",
  "fund.publicWebsite": "Public Website",
  "fund.websitePh": "example.com",
  "fund.widgetBgColor": "Widget Background Color",
  "fund.widgetTextColor": "Widget Text Color",

  // News page
  "news.title": "News",
  "news.postPlaceholder": "What's new? Share an update with your supporters...",
  "news.posting": "Posting...",
  "news.post": "Post",
  "news.filters": "Filters",
  "news.allWallets": "All wallets",
  "news.allFunds": "All funds",
  "news.from": "From",
  "news.to": "To",
  "news.clearFilters": "Clear filters",
  "news.loadingPosts": "Loading posts...",
  "news.noPosts": "No posts yet. Share your first update!",
  "news.deleteTitle": "Delete Post",
  "news.deleteMsg":
    "Are you sure you want to delete this post? This action cannot be undone.",

  // Settings page
  "settings.title": "Settings",
  "settings.apiKey": "API Key",
  "settings.apiKeyDesc":
    "Your API key is stored locally in the browser. Clear it to disconnect and require re-authentication.",
  "settings.datetimeFormat": "Date and Time Format",
  "settings.datetimeDesc":
    "This setting affects how dates and times are displayed on the dashboard and in all PDF/XML reports.",
  "settings.examplePatterns": "Example patterns:",
  "settings.formatPattern": "Format pattern",
  "settings.update": "Update",
  "settings.saving": "Saving...",
  "settings.notSet": "Not set",
  "settings.languageDesc": "Choose the interface language. Your choice is saved on this device and in the server settings.",

  // Widget page
  "widget.noFundDesc": "Create a fund first to configure its public widget.",
  "widget.title": "Widget Settings",
  "widget.subtitlePrefix": "Configure and embed the public widget for",
  "widget.styleSettings": "Style Settings",
  "widget.styleDesc": "Customize the appearance of the embedded widget. Colors are saved per-fund.",
  "widget.bgColor": "Background Color",
  "widget.bgColorDesc": "The base color for the widget gradient. The gradient will transition from this color to a shifted hue variant.",
  "widget.textColor": "Text Color",
  "widget.textColorDesc": "The color used for all text and the progress bar inside the widget.",
  "widget.saveSettings": "Save Settings",

  // Color picker
  "colorpicker.presets": "Preset Colors",
  "colorpicker.hue": "Hue",
  "colorpicker.hexColor": "Hex Color",
  "colorpicker.invalidHex": "Invalid hex color. Use format: #aabbcc",

  // Widget preview
  "widgetpreview.title": "Public Widget",
  "widgetpreview.desc": "This widget shows your total received balance publicly. Anyone with the link can view it.",
  "widgetpreview.updatedJustNow": "Updated: just now",
  "widgetpreview.embedCodeLabel": "Embed code:",
  "widgetpreview.jsonApiLabel": "JSON API:",
};

export default en;