/* ============================
   1. TRADUCTIONS & BADGES
============================ */
const translations = {
    fr: {
        title: "Dashboard Analytique",
        subtitle: "Sélectionnez un formulaire ci-dessous pour voir l'analyse détaillée.",
        responses: "Réponses",
        search_ph: "Rechercher...",
        btn_search: "Filtrer",
        label_month: "Mois",
        opt_all: "Tous les mois",
        opt_all_teachers: "Tous les enseignants",
        label_teacher: "Enseignant",
        label_status: "Statut",
        opt_present: "Présent (P)",
        opt_absent: "Absent (A)",
        opt_late: "Retard (R)",
        btn_reset: "Réinitialiser",
        btn_prev: "Précédent",
        btn_next: "Suivant",
        page_num: "Page",
        btn_text: "العربية",
        chart_bar: "Top Absences",
        chart_line: "Évolution",
        chart_pie: "Répartition",
        menu_home: "Accueil",
        menu_blog: "Blog",
        flag: "🇫🇷"
    },
    ar: {
        title: "لوحة التحكم والتحليل",
        subtitle: "حدد نموذجًا أدناه لمشاهدة التحليل التفصيلي.",
        responses: "إجابات",
        search_ph: "بحث...",
        btn_search: "بحث",
        label_month: "الشهر",
        opt_all: "كل الأشهر",
        opt_all_teachers: "كل الأساتذة",
        label_teacher: "المعلم",
        label_status: "الحالة",
        opt_present: "حاضر (P)",
        opt_absent: "غائب (A)",
        opt_late: "تأخر (R)",
        btn_reset: "إعادة تعيين",
        btn_prev: "السابق",
        btn_next: "التالي",
        page_num: "صفحة",
        btn_text: "Français",
        chart_bar: "أعلى الغيابات",
        chart_line: "التطور",
        chart_pie: "التوزيع",
        menu_home: "الرئيسية",
        menu_blog: "المدونة",
        flag: "🇲🇷"
    }
};

const badgeData = {
    P: { fr: "Présent", ar: "حاضر", icon: "fa-check", class: "badge-success" },
    A: { fr: "Absent", ar: "غائب", icon: "fa-xmark", class: "badge-danger" },
    R: { fr: "Retard", ar: "تأخر", icon: "fa-clock", class: "badge-warning" }
};

let currentLang = "fr";

/* ============================
   2. LANGUE
============================ */
function updateLangButton() {
    const btn = document.getElementById("lang-btn");
    if (!btn) return;
    btn.innerHTML = `
        <span style="font-size:1.4em">${translations[currentLang].flag}</span>
        <span style="margin-inline:8px">${translations[currentLang].btn_text}</span>
    `;
}

function toggleLanguage() {
    currentLang = currentLang === "fr" ? "ar" : "fr";

    document.documentElement.lang = currentLang;
    document.documentElement.dir = currentLang === "ar" ? "rtl" : "ltr";
    document.body.classList.toggle("lang-ar", currentLang === "ar");

    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.dataset.i18n;
        if (translations[currentLang][key]) {
            el.innerText = translations[currentLang][key];
        }
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
        const key = el.dataset.i18nPlaceholder;
        if (translations[currentLang][key]) {
            el.placeholder = translations[currentLang][key];
        }
    });

    refreshBadges();
    updateLangButton();
}

/* ============================
   3. BADGES STATUT
============================ */
function beautifyTable() {
    document.querySelectorAll("td[data-status]").forEach(cell => {
        const val = cell.dataset.status;
        if (!badgeData[val]) return;

        const d = badgeData[val];
        cell.innerHTML = `
            <span class="status-badge ${d.class}">
                <i class="fa-solid ${d.icon}"></i> ${d[currentLang]}
            </span>
        `;
    });
}

function refreshBadges() {
    document.querySelectorAll("td[data-status]").forEach(cell => {
        const val = cell.dataset.status;
        if (!badgeData[val]) return;

        const d = badgeData[val];
        cell.innerHTML = `
            <span class="status-badge ${d.class}">
                <i class="fa-solid ${d.icon}"></i> ${d[currentLang]}
            </span>
        `;
    });
}

/* ============================
   4. IMAGES KOBO
============================ */
function loadImages() {
    document.querySelectorAll("td[data-image]").forEach(cell => {
        let data;
        try {
            data = JSON.parse(cell.dataset.image);
        } catch {
            return;
        }

        const medium = data.download_medium_url;
        const original = data.download_url;
        const filename = data.filename || "Image";

        if (!medium) return;

        const id = "img-" + Math.random().toString(36).slice(2);
        cell.innerHTML = `
            <a href="${original}" target="_blank" id="${id}">
                <div class="img-loader">
                    <i class="fa-solid fa-spinner fa-spin"></i>
                </div>
            </a>
        `;

        const img = new Image();
        img.src = medium;

        img.onload = () => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = `<img src="${medium}" class="table-img" alt="${filename}">`;
        };

        img.onerror = () => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = `<i class="fa-solid fa-image-slash text-danger"></i>`;
        };
    });
}

/* ============================
   5. MENU MOBILE
============================ */
function toggleMenu() {
    const menu = document.getElementById("navLinks");
    if (menu) menu.classList.toggle("active");
}

document.addEventListener("click", e => {
    const nav = document.querySelector(".navbar");
    const menu = document.getElementById("navLinks");
    if (menu && nav && !nav.contains(e.target)) {
        menu.classList.remove("active");
    }
});

/* ============================
   6. INIT
============================ */
document.addEventListener("DOMContentLoaded", () => {
    updateLangButton();
    beautifyTable();
    loadImages();
});

document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("userDropdown");
    const menu = document.getElementById("userDropdownMenu");

    if (btn && menu) {
        btn.addEventListener("click", function (e) {
            e.stopPropagation(); // 🔥 empêche la fermeture automatique
            menu.classList.toggle("show");
        });

        document.addEventListener("click", function () {
            menu.classList.remove("show");
        });
    }
});


    function toggleLanguage() {
        const btn = document.getElementById('lang-btn');
        let currentLang = btn.innerText;
        currentLang = currentLang === 'Ar' ? 'Fr' : 'Ar';
        btn.innerText = currentLang;
    }