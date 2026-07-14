import type { Messages } from "../types";

const be: Messages = {
  // Language switcher / language names
  "language.label": "Мова",
  "language.en": "English",
  "language.es": "Español",
  "language.ptBR": "Português",
  "language.fr": "Français",
  "language.de": "Deutsch",
  "language.uk": "Українська",
  "language.be": "Беларуская",
  "language.ru": "Русский",

  // App / nav
  "app.title": "XMR Fund Transparency Suite",
  "nav.news": "Навіны",
  "nav.wallets": "Гаманцы",
  "nav.settings": "Налады",
  "nav.disconnect": "Выйсці",
  "nav.menu": "Меню",

  // Common
  "common.active": "Актыўны",
  "common.inactive": "Неактыўны",
  "common.refresh": "Абнавіць",
  "common.refreshing": "Абнаўленне...",
  "common.loading": "Загрузка...",
  "common.cancel": "Адмена",
  "common.delete": "Выдаліць",
  "common.edit": "Рэдагаваць",
  "common.save": "Захаваць",
  "common.saving": "Захаванне...",
  "common.creating": "Стварэнне...",
  "common.copied": "Скапіравана!",
  "common.failed": "Памылка",
  "common.copyAddress": "Скапіраваць адрас",
  "common.copyEmbedCode": "Скапіраваць код устаўкі",
  "common.copyUrl": "Скапіраваць URL",
  "common.processing": "Апрацоўка...",
  "common.retry": "Паўтарыць",
  "common.optional": "неабавязкова",
  "common.wallet": "Гаманец",
  "common.fund": "Фонд",
  "common.description": "Апісанне",
  "common.confirm": "Пацвердзіць",
  "common.activate": "Актываваць",
  "common.deactivate": "Дэактываваць",
  "common.activating": "Актывацыя...",
  "common.deactivating": "Дэактывацыя...",
  "common.selectWallet": "Абраць гаманец",
  "common.selectFund": "Абраць фонд",
  "common.createFund": "Стварыць фонд",
  "common.saveChanges": "Захаваць змены",
  "common.deleteFund": "Выдаліць фонд",
  "common.failedLoadWallets": "Не ўдалося загрузіць гаманцы",
  "common.failedDeleteWallet": "Не ўдалося выдаліць гаманец",
  "common.failedCreateWallet": "Не ўдалося стварыць гаманец",
  "common.failedUpdateFormat": "Не ўдалося абнавіць фармат",

  // Login screen
  "login.connectTitle": "Падключыцца да панэлі",
  "login.description":
    "Увядзіце API-ключ, наладжаны падчас разгортвання. Гэты ключ аўтарызуе ўсе запыты да бэкенда.",
  "login.apiKey": "API-ключ",
  "login.apiKeyPlaceholder": "Увядзіце ваш API-ключ...",
  "login.validating": "Праверка...",
  "login.connect": "Падключыцца",
  "login.privacyNote":
    "API-ключ захоўваецца лакальна ў вашым браўзеры і ніколі не перадаецца трэцім асобам.",

  // Dashboard
  "dashboard.loadingData": "Загрузка даных...",
  "dashboard.errorLoadingTitle": "Памылка загрузкі даных",
  "dashboard.noWalletTitle": "Гаманец не наладжаны",
  "dashboard.noWalletDesc":
    "Стварыце гаманец і фонд, каб пачаць адсочваць уваходныя ахвяраванні Monero.",
  "dashboard.goToWallets": "Да гаманцоў",
  "dashboard.noFundTitle": "Фонд не наладжаны",
  "dashboard.noFundDesc":
    "У гэтага гаманца яшчэ няма фондаў. Стварыце фонд, каб пачаць адсочваць ахвяраванні.",
  "dashboard.loadingWallet": "Загрузка даных гаманца...",

  // Fund card
  "fundcard.scanError": "Памылка сканавання",
  "fundcard.scanning": "Сканаванне",
  "fundcard.totalReceived": "Агулам атрымана",
  "fundcard.target": "Мэта",
  "fundcard.transactions": "Транзакцыі",
  "fundcard.lastScan": "Апошняе сканаванне",
  "fundcard.never": "Ніколі",
  "fundcard.blockHeight": "Вышыня блока:",
  "fundcard.notStarted": "Не пачата",
  "fundcard.scanErrorTitle": "Памылка сканавання",

  // Transaction table
  "txtable.title": "Апошнія транзакцыі",
  "txtable.collapse": "Згарнуць",
  "txtable.showAll": "Паказаць усе ({count})",
  "txtable.colDate": "Дата",
  "txtable.colAmount": "Сума",
  "txtable.colConfirmations": "Пацверджанні",
  "txtable.colHeight": "Вышыня",
  "txtable.colTxid": "TXID",
  "txtable.noMatch": "Ніводная транзакцыя не адпавядае бягучым фільтрам.",

  // Filters
  "filters.title": "Фільтры і сартаванне",
  "filters.reset": "Скінуць фільтры",
  "filters.startDate": "Дата пачатку",
  "filters.endDate": "Дата канца",
  "filters.amountTier": "Памер сумы",
  "filters.sortBy": "Сартаваць па",
  "filters.addSort": "Дадаць сартаванне",
  "filters.noSorting":
    "Сартаванне не прыменена (па змаўчанні: вышыня блока па ўбыванні)",
  "filters.descending": "Па ўбыванні",
  "filters.ascending": "Па ўзрастанні",

  // Tiers
  "tier.micro": "Мікра",
  "tier.medium": "Сярэдні",
  "tier.large": "Вялікі",
  "tier.whale": "Кіт",
  "tierDesc.micro": "< 0,1 XMR",
  "tierDesc.medium": "0,1 — 1,0 XMR",
  "tierDesc.large": "1,0 — 5,0 XMR",
  "tierDesc.whale": "> 5,0 XMR",

  // Sort fields
  "sortField.timestamp": "Дата",
  "sortField.amount_xmr": "Сума",
  "sortField.confirmations": "Пацверджанні",

  // Charts
  "charts.cumulativeReceived": "Кумулятыўна атрымана XMR",
  "charts.linear": "Лінейны",
  "charts.log": "Лагарыфмічны",
  "charts.noData": "Даных пра транзакцыі яшчэ няма",
  "charts.donationSize": "Сегментацыя па памеры ахвяравання",
  "charts.goalProgress": "Мэта і прагрэс",
  "charts.bar": "Слупок",
  "charts.gauge": "Шкала",
  "charts.noTargetConfigured":
    "Для гэтага фонда не наладжана мэта фінансавання. Вы можаце наладзіць яе ў",
  "charts.noTargetSettingsLink": "Наладах",
  "charts.noTargetSuffix": ".",
  "charts.volumeDistribution": "Размеркаванне аб'ёму XMR",
  "charts.received": "Атрымана",
  "charts.remaining": "Засталося",
  "charts.cumulativeXmr": "Кумулятыўны XMR",
  "charts.target": "Мэта",
  "charts.xmrVolume": "Аб'ём XMR",
  "charts.donations": {
    one: "{count} ахвяраванне",
    few: "{count} ахвяраванні",
    many: "{count} ахвяраванняў",
    other: "{count} ахвяравання",
  },

  // Wallets page
  "wallets.title": "Гаманцы",
  "wallets.subtitle":
    "Кіруйце сваімі гаманцамі толькі для прагляду. Кожны гаманец можа мець некалькі фондаў з уласнымі адрасамі для папаўнення.",
  "wallets.createWallet": "Стварыць гаманец",
  "wallets.loadingWallets": "Загрузка гаманцоў...",
  "wallets.errorLoadingTitle": "Памылка загрузкі гаманцоў",
  "wallets.setUpWallet": "Наладзьце свой гаманец",
  "wallets.createNew": "Стварыць новы гаманец",
  "wallets.createDesc":
    "Падключыце гаманец Monero толькі для прагляду, падаўшы яго асноўны адрас і прыватны ключ прагляду. Гэта інфармацыя шыфруецца перад захаваннем.",
  "wallets.walletName": "Назва гаманца",
  "wallets.walletNamePh": "Мой гаманец Monero",
  "wallets.walletNameHint": "Назва для адлюстравання гэтага гаманца.",
  "wallets.primaryAddress": "Асноўны адрас",
  "wallets.primaryAddressHint":
    "Асноўны адрас Monero вашага гаманца (95 сімвалаў, пачынаецца з 4/8/A/B).",
  "wallets.viewKey": "Прыватны ключ прагляду",
  "wallets.viewKeyPh": "64 шаснаццатковыя сімвалы",
  "wallets.viewKeyHint": "Прыватны ключ прагляду вашага гаманца (64 шаснаццатковыя сімвалы).",
  "wallets.neverShareSpend": "Ніколі не дзяліцеся сваім ключом расходавання.",
  "wallets.startHeight": "Стартавая вышыня",
  "wallets.startHeightHint":
    "Вышыня блока, з якой пачынаецца сканаванне. Ніжэй = больш гісторыі, вышэй = хутчэйшая сінхранізацыя.",
  "wallets.created": "Створаны",
  "wallets.lastScannedHeight": "Апошняя прасканаваная вышыня",
  "wallets.lastScanAt": "Апошняе сканаванне",
  "wallets.scanError": "Памылка сканавання",
  "wallets.settingsFunds": "Налады і фонды",
  "wallets.confirmDeleteTitle": "Пацвердзіць выдаленне",
  "wallets.confirmDeleteMsg":
    "Вы ўпэўненыя, што хочаце выдаліць гаманец {name}?",
  "wallets.deleteWallet": "Выдаліць гаманец",
  "wallets.deleting": "Выдаленне...",
  "wallets.deleteWarning":
    "Усе звязаныя фонды, транзакцыі і допісы будуць назаўсёды выдалены. Гэта дзеянне нельга адмяніць.",

  // Wallet detail
  "walletdetail.loading": "Загрузка гаманца...",
  "walletdetail.errorTitle": "Памылка загрузкі гаманца",
  "walletdetail.notFoundTitle": "Гаманец не знойдзены",
  "walletdetail.notFoundDesc":
    "Гаманец, які вы шукаеце, не існуе або быў выдалены.",
  "walletdetail.backToWallets": "Назад да гаманцоў",
  "walletdetail.walletSettings": "Налады гаманца",
  "walletdetail.funds": "Фонды",
  "walletdetail.colNumber": "№",
  "walletdetail.colLabel": "Назва",
  "walletdetail.colTarget": "Мэта",
  "walletdetail.colReceived": "Атрымана",
  "walletdetail.colStatus": "Статус",
  "walletdetail.colActions": "Дзеянні",
  "walletdetail.manage": "Кіраваць",
  "walletdetail.noFunds": "Фондаў яшчэ няма. Стварыце адзін, каб пачаць.",
  "walletdetail.loadingFunds": "Загрузка фондаў...",
  "walletdetail.deactivateWallet": "Дэактываваць гаманец",
  "walletdetail.activateWallet": "Актываваць гаманец",
  "walletdetail.deactivateMsg":
    "Вы ўпэўненыя, што хочаце дэактываваць гэты гаманец? Сканер спыніць апрацоўку гэтага гаманца.",
  "walletdetail.activateMsg":
    "Вы ўпэўненыя, што хочаце актываваць гэты гаманец? Сканер адновіць апрацоўку.",

  // Fund detail
  "funddetail.loading": "Загрузка даных фонда...",
  "funddetail.errorTitle": "Памылка загрузкі фонда",
  "funddetail.notFoundTitle": "Фонд не знойдзены",
  "funddetail.notFoundDesc":
    "Фонд, які вы шукаеце, не існуе або ў вас няма доступу.",
  "funddetail.backToWallets": "Назад да гаманцоў",
  "funddetail.fundSettings": "Налады фонда",
  "funddetail.widgetPreview": "Папярэдні прагляд і ўстаўка віджэта",
  "funddetail.printPng": "Экспартаваць у PNG",
  "funddetail.businessCard": "Візітка",
  "funddetail.wide": "Шырокі",
  "funddetail.vertical": "Вертыкальны",
  "funddetail.widgetDesc":
    "Гэты віджэт публічна паказвае ваш фонд. Любы, хто мае спасылку, можа яго паглядзець.",
  "funddetail.loadingWidget": "Загрузка даных віджэта...",
  "funddetail.updated": "Абноўлена:",
  "funddetail.copyAddress": "Скапіраваць адрас",
  "funddetail.poweredBy": "Widget powered by xmrfts.com",
  "funddetail.news": "Навіны",
  "funddetail.loadingNews": "Загрузка...",
  "funddetail.failedNews": "Не ўдалося загрузіць навіны",
  "funddetail.noNews": "Навін яшчэ няма",
  "funddetail.loadMore": "Загрузіць яшчэ",
  "funddetail.embedCode": "Код устаўкі",
  "funddetail.widgetJsonUrl": "URL JSON віджэта",
  "funddetail.widgetCacheNote":
    "Віджэт кэшуецца 60 секунд і мае абмежаванне 60 запытаў за хвіліну на IP.",
  "funddetail.deleteTitle": "Выдаліць фонд",
  "funddetail.deleteSubtitle": "Гэта дзеянне нельга адмяніць.",
  "funddetail.deleteMsg":
    "Вы ўпэўненыя, што хочаце выдаліць {label}? Усе звязаныя транзакцыі і допісы будуць назаўсёды выдалены.",
  "funddetail.deactivateFund": "Дэактываваць фонд",
  "funddetail.activateFund": "Актываваць фонд",
  "funddetail.deactivateSubtitle": "Гэта спыніць адсочванне новых транзакцый.",
  "funddetail.activateSubtitle":
    "Гэта адновіць адсочванне новых транзакцый.",
  "funddetail.deactivateMsg":
    "Вы ўпэўненыя, што хочаце дэактываваць гэты фонд? Ён больш не з'яўляецца ў публічных віджэтах і не будзе атрымліваць абнаўленні сканавання.",
  "funddetail.activateMsg":
    "Вы ўпэўненыя, што хочаце актываваць гэты фонд? Ён зноў з'яўляецца ў публічных віджэтах і будзе атрымліваць абнаўленні сканавання.",
  "funddetail.depositAddressHint":
    "Змена адраса папаўнення прывядзе да поўнага перасканавання блокчейна.",
  "funddetail.websiteHint": "Увядзіце без https:// — напр. example.com",

  "funddetail.staticWidget": "Статычны аўтаномны віджэт",
  "funddetail.staticWidgetDesc": "Віджэт без запытаў — усе даныя ўбудаваны ў сніпет. Ніякіх зваротаў да сервера, без выкрыцця URL вашай панэлі.",
  "funddetail.staticWidgetLoading": "Генерацыя QR-кода...",
  "funddetail.staticEmbedCode": "Статычны код устаўкі",
  "funddetail.staticWidgetNote": "Гэты віджэт — здымак стану, ён не абнаўляецца аўтаматычна. Перагенеруйце яго пасля змен, каб адлюстраваць найноўшыя налады фонда.",
  "funddetail.copyStaticEmbed": "Скапіраваць код устаўкі",

  // Fund form fields
  "fund.label": "Назва",
  "fund.labelPh": "Назва кампаніі",
  "fund.labelPh2": "Мой збор сродкаў",
  "fund.descriptionPh": "Для чаго гэты фонд?",
  "fund.descriptionPh2": "Опішыце прызначэнне гэтага фонда...",
  "fund.depositAddress": "Адрас папаўнення",
  "fund.depositAddressPh": "4...",
  "fund.depositAddressPh2": "86erTZz...",
  "fund.targetAmount": "Мэтавая сума (XMR)",
  "fund.targetAmountPh": "0,00",
  "fund.targetAmountPh2": "напр. 100,00",
  "fund.publicWebsite": "Публічны сайт",
  "fund.websitePh": "example.com",
  "fund.widgetBgColor": "Колер фону віджэта",
  "fund.widgetTextColor": "Колер тэксту віджэта",

  // News page
  "news.title": "Навіны",
  "news.postPlaceholder": "Што новага? Падзяліцеся абнаўленнем з прыхільнікамі...",
  "news.posting": "Публікацыя...",
  "news.post": "Апублікаваць",
  "news.filters": "Фільтры",
  "news.allWallets": "Усе гаманцы",
  "news.allFunds": "Усе фонды",
  "news.from": "Ад",
  "news.to": "Да",
  "news.clearFilters": "Ачысціць фільтры",
  "news.loadingPosts": "Загрузка допісаў...",
  "news.noPosts": "Допісаў яшчэ няма. Падзяліцеся першым абнаўленнем!",
  "news.deleteTitle": "Выдаліць допіс",
  "news.deleteMsg":
    "Вы ўпэўненыя, што хочаце выдаліць гэты допіс? Гэта дзеянне нельга адмяніць.",

  // Settings page
  "settings.title": "Налады",
  "settings.apiKey": "API-ключ",
  "settings.apiKeyDesc":
    "Ваш API-ключ захоўваецца лакальна ў браўзеры. Ачысціце яго, каб адключыцца і запатрабаваць паўторную аўтэнтыфікацыю.",
  "settings.datetimeFormat": "Фармат даты і часу",
  "settings.datetimeDesc":
    "Гэта налада ўплывае на тое, як даты і час адлюстроўваюцца на панэлі і ва ўсіх справаздачах PDF/XML.",
  "settings.examplePatterns": "Прыклады шаблонаў:",
  "settings.formatPattern": "Шаблон фармату",
  "settings.update": "Абнавіць",
  "settings.saving": "Захаванне...",
  "settings.notSet": "Не зададзены",
  "settings.languageDesc": "Абярыце мову інтэрфейсу. Ваш выбар захоўваецца на гэтым прыладзе і ў наладах сервера.",

  // Widget page
  "widget.noFundDesc": "Спачатку стварыце фонд, каб наладзіць яго публічны віджэт.",
  "widget.title": "Налады віджэта",
  "widget.subtitlePrefix": "Наладзьце і ўстаўце публічны віджэт для",
  "widget.styleSettings": "Налады стылю",
  "widget.styleDesc": "Наладзьце знешні выгляд убудаванага віджэта. Колеры захоўваюцца для кожнага фонда асобна.",
  "widget.bgColor": "Колер фону",
  "widget.bgColorDesc": "Базавы колер для градыента віджэта. Градыент будзе пераходзіць ад гэтага колеру да змешчанага адцення.",
  "widget.textColor": "Колер тэксту",
  "widget.textColorDesc": "Колер для ўсяго тэксту і паласы прагрэсу ўнутры віджэта.",
  "widget.saveSettings": "Захаваць налады",

  // Color picker
  "colorpicker.presets": "Палітра колераў",
  "colorpicker.hue": "Адценне",
  "colorpicker.hexColor": "Шаснаццатковы колер",
  "colorpicker.invalidHex": "Няправільны шаснаццатковы колер. Выкарыстоўвайце фармат: #aabbcc",

  // Widget preview
  "widgetpreview.title": "Публічны віджэт",
  "widgetpreview.desc": "Гэты віджэт публічна паказвае вашу агульную атрыманую суму. Любы, хто мае спасылку, можа яго паглядзець.",
  "widgetpreview.updatedJustNow": "Абноўлена: толькі што",
  "widgetpreview.embedCodeLabel": "Код устаўкі:",
  "widgetpreview.jsonApiLabel": "JSON API:",
};

export default be;