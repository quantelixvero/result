// Global variables
let studentsData = [];
let cleanData = {};
let allSubjects = [];
let isCompactView = true;
let currentDetailSubject = null;
let currentDetailRow = null;
let currentSort = 'roll';
let sortDirection = 'asc';
// declare globally
let jsonKey = null;
let jsonPath = null;
document.addEventListener("DOMContentLoaded", async () => {
    const params = new URLSearchParams(window.location.search);
    jsonKey = params.get("json");

    if (!jsonKey) {
        alert("No exam data provided");
        return;
    }

    jsonKey = jsonKey.toLowerCase();
    jsonPath = `/results-file/${jsonKey}.json`;

    try {
        await loadData();           // fetch + process
        populateSortOptions();      // build dropdown
        document.getElementById("sortSelect").value = `${currentSort}|${sortDirection}`;
        handleSort();
        renderSectionSummary();
        renderSubjectCards();
        setupEventListeners();      // attach listeners

        // exam name
        let fileName = jsonPath.split("/").pop().replace(".json", "");
        let parts = fileName.split(".");
        const examNameDiv = document.getElementById("exam-name");
        function capitalizeWords(str) {
            return str.replace(/\b\w/g, char => char.toUpperCase());
        }
        examNameDiv.innerHTML = `
          <h4>${capitalizeWords(parts[0])}</h4>
          <h3>${parts.slice(1).map(capitalizeWords).join(" | ")}</h3>
        `;
    } catch (err) {
        console.error("Error loading data:", err);
    }
});



function getCurrentFilteredEntries() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase().trim();
    let entries = Object.entries(cleanData);
    if (!searchValue) return entries;
    return entries.filter(([roll, data]) =>
        String(roll).includes(searchValue) ||
        (data.name && data.name.toLowerCase().includes(searchValue))
    );
}

function handleSort() {
    // read select value; fallback to currentSort/direction
    const sel = document.getElementById('sortSelect').value || `${currentSort}|${sortDirection}`;
    const [field, dir] = sel.split('|');
    currentSort = field || currentSort;
    sortDirection = dir || sortDirection;

    const entries = getCurrentFilteredEntries();
    const sorted = sortEntries(entries, currentSort, sortDirection);
    renderTableFromEntries(sorted);

    // DEBUG: show top results and their normalized values
    try {
        const top = sorted.slice(0, 12).map(([r, s]) => {
            const raw = allSubjects.includes(currentSort)
                ? s.subjects?.[currentSort]?.termTotal ?? null
                : (currentSort === 'name' ? s.name : currentSort === 'roll' ? s.roll : currentSort === 'gpa' ? s.gpa : currentSort === 'totalMark' ? s.totalMark : currentSort === 'global' ? s.ranking?.global : s.ranking?.section);
            return { roll: r, name: s.name, raw, normalized: normalizeForSort(raw, currentSort) };
        });
        console.log(`Sorted by ${currentSort} (${sortDirection}) — top entries:`, top);
    } catch (e) { /* ignore debug errors */ }
}

// helper used by sorter & debug
function normalizeForSort(raw, field) {
    // fields considered numeric
    const numericFields = ['roll', 'gpa', 'gpaWithoutAdditional', 'totalMark', 'Rank', 'section'];
    const isSubject = allSubjects.includes(field);
    const isNumeric = isSubject || numericFields.includes(field);

    if (raw === null || raw === undefined) return null;

    // numbers are fine as-is
    if (typeof raw === 'number') {
        return isNumeric ? (Number.isFinite(raw) ? raw : null) : String(raw).toLowerCase();
    }

    // cast to string and trim
    let s = String(raw).trim();
    if (s === '') return null;

    // normalize common "empty" markers & dash variants
    const sLow = s.toLowerCase();
    const alwaysBottomSet = new Set([
        '-', '—', '–', '−', // different dash characters
        'absent', 'not qualified', 'n/a', 'na', 'none', 'null', 'undefined'
    ]);
    if (alwaysBottomSet.has(sLow)) return null;

    // numeric fields: try parse (drop commas)
    if (isNumeric) {
        // remove commas and percent sign if present
        const cleaned = s.replace(/,/g, '').replace('%', '');
        const n = parseFloat(cleaned);
        return Number.isFinite(n) ? n : null; // non-numeric text -> null (bottom)
    }

    // non-numeric: use lowercase for stable string compare
    return sLow;
}
function sortEntries(entries, field, direction = 'asc') {
    const isSubject = allSubjects.includes(field);
    const numericFields = ['roll', 'gpa', 'gpaWithoutAdditional', 'totalMark', 'global', 'section'];
    const isNumericField = (f) => isSubject || numericFields.includes(f);
    const dir = (direction === 'desc') ? 'desc' : 'asc';

    const normalize = (raw, numeric) => {
        if (raw === null || raw === undefined) return null;

        if (typeof raw === 'number') {
            return numeric ? (Number.isFinite(raw) ? raw : null) : String(raw).toLowerCase();
        }

        let s = String(raw).trim();
        if (s === '') return null;

        const sLow = s.toLowerCase();

        const alwaysBottom = new Set([
            '-', '—', '–', '−',
            'absent', 'not qualified',
            'n/a', 'na', 'none', 'null', 'undefined'
        ]);
        if (alwaysBottom.has(sLow)) return null;

        if (numeric) {
            const cleaned = s.replace(/,/g, '').replace('%', '');
            const n = parseFloat(cleaned);
            return Number.isFinite(n) ? n : null;
        }

        return sLow;
    };

    return entries.slice().sort(([kA, a], [kB, b]) => {
        let rawA, rawB;
        if (isSubject) {
            rawA = a.subjects?.[field]?.termTotal ?? null;
            rawB = b.subjects?.[field]?.termTotal ?? null;
        } else {
            switch (field) {
                case 'roll': rawA = a.roll; rawB = b.roll; break;
                case 'name': rawA = a.name; rawB = b.name; break;
                case 'gpa': rawA = a.gpa; rawB = b.gpa; break;
                case 'gpaWithoutAdditional': rawA = a.gpaWithoutAdditional; rawB = b.gpaWithoutAdditional; break;
                case 'totalMark': rawA = a.totalMark; rawB = b.totalMark; break;
                case 'global': rawA = a.ranking?.global; rawB = b.ranking?.global; break;
                case 'section': rawA = a.ranking?.section; rawB = b.ranking?.section; break;
                default: rawA = ''; rawB = '';
            }
        }

        const numeric = isNumericField(field);

        // 🚨 Only force absent/not-qualified to bottom if field is NOT roll/name
        const statusA = String((a.status || '')).trim().toLowerCase();
        const statusB = String((b.status || '')).trim().toLowerCase();
        const forceBottom = !(field === 'roll' || field === 'name');

        const isAAbsentOrNotQualified = forceBottom && (statusA === 'absent' || statusA === 'not qualified');
        const isBAbsentOrNotQualified = forceBottom && (statusB === 'absent' || statusB === 'not qualified');

        const A = isAAbsentOrNotQualified ? null : normalize(rawA, numeric);
        const B = isBAbsentOrNotQualified ? null : normalize(rawB, numeric);

        if (A === null && B === null) return 0;
        if (A === null && B !== null) return 1;
        if (A !== null && B === null) return -1;

        if (numeric) {
            if (A < B) return dir === 'asc' ? -1 : 1;
            if (A > B) return dir === 'asc' ? 1 : -1;
            return 0;
        }

        if (A < B) return dir === 'asc' ? -1 : 1;
        if (A > B) return dir === 'asc' ? 1 : -1;
        return 0;
    });
}


function getHighlightClass(value, type, subject = null) {
    const subNumber = 20;

    if (type === 'gpa') {
        if (parseFloat(value) === 0.00) return 'danger';
        if (parseFloat(value) === 5.00) return 'good';
    }

    if (type === 'ranking') {
        if (subject.gpa === 0.00) return 'danger';
        if (subject.gpa === 5.00) return 'good';
    }

    if (type === 'termTotal') {
        if (subject.grade === 'F') return 'danger';
        if (subject.grade === 'A-') return 'good';
    }

    if (type === 'cq') {
        if (value === 'A') return 'warning';
        if (parseFloat(value) < subNumber / 2) return 'danger';
        if (parseFloat(value) > subNumber * 0.8) return 'good';
    }

    if (type === 'mcq') {
        if (parseFloat(value) < (subNumber / 4) / 2) return 'danger';
        if (parseFloat(value) > (subNumber / 4) * 0.8) return 'good';
    }

    if (type === 'prac') {
        if (parseFloat(value) < (subNumber / 4) / 2) return 'danger';
        if (parseFloat(value) > (subNumber / 4) * 0.8) return 'good';
    }

    return '';
}



// --- NEW: render table from an entries array (sorted or not)
function renderTableFromEntries(entries) {
    const table = document.getElementById('resultsTable');
    const header = document.getElementById('tableHeader');
    const body = document.getElementById('tableBody');

    header.innerHTML = '';
    body.innerHTML = '';

    createTableHeader(header);

    entries.forEach(([roll, student], index) => {
        createTableRow(body, student, index);
    });

    // padding rows
    if (entries.length < 8) {
        for (let i = entries.length; i < 8; i++) createEmptyRow(body, i);
    }
}


// --- UPDATED: search should just re-run the sort+render pipeline
function handleSearch() {
    // no complex filtering here — handleSort reads the search input
    handleSort();
}



// Load student data
// Load student data
async function loadData() {
    try {
        const response = await fetch(jsonPath);
        studentsData = await response.json();
        processData();

    } catch (error) {
        console.error('Error loading data:', error);
    }
}


// Process raw data into clean format
function processData() {
    cleanData = {};
    allSubjects = new Set();

    studentsData.forEach(student => {
        const roll = student.roll.toString();
        // inside processData(), when creating cleanData[roll]
        cleanData[roll] = {
            roll: (student.roll !== undefined && student.roll !== null) ? student.roll : null,
            name: student.name || '',
            section: student.Section || '',
            status: student.status || 'qualified',
            // keep numeric fields null when missing so sort can push them down
            gpa: (student.gpa !== undefined && student.gpa !== null && student.gpa !== '') ? Number(student.gpa) : null,
            gpaWithoutAdditional: (student.gpaWithoutAdditional !== undefined && student.gpaWithoutAdditional !== null && student.gpaWithoutAdditional !== '') ? Number(student.gpaWithoutAdditional) : null,
            totalMark: (student.totalMark !== undefined && student.totalMark !== null && student.totalMark !== '') ? Number(student.totalMark) : null,
            ranking: {
                global: (student.Ranking && student.Ranking.global !== undefined && student.Ranking.global !== null && student.Ranking.global !== '') ? Number(student.Ranking.global) : null,
                section: (student.Ranking && student.Ranking.section !== undefined && student.Ranking.section !== null && student.Ranking.section !== '') ? Number(student.Ranking.section) : null
            },
            url: student.url || '',
            subjects: {},
            optionalSubject: student.optionalSubject || null
        };


        // Process subjects
        Object.keys(student).forEach(key => {
            if (typeof student[key] === 'object' && student[key] !== null &&
                !['Ranking'].includes(key) && student[key].termTotal !== undefined) {
                allSubjects.add(key);
                // when populating cleanData[roll].subjects[subjectName]...
                cleanData[roll].subjects[key] = {
                    cq: student[key].cq ?? '',
                    mcq: student[key].mcq ?? '',
                    practical: student[key].practical ?? '',
                    termTotal: student[key].termTotal ?? '',   // <- NOT '0'
                    grade: student[key].grade ?? 'F',
                    gp: (student[key].gp !== undefined && student[key].gp !== null && student[key].gp !== '') ? parseFloat(student[key].gp) : null
                };

            }
        });
    });

    allSubjects = Array.from(allSubjects);
}

// Setup event listeners
// Setup event listeners
// Setup event listeners
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const sortSelect = document.getElementById('sortSelect');
    const compactToggle = document.getElementById('compactToggle');

    // search only when button is clicked
    searchButton.addEventListener('click', () => {
        handleSearch(searchInput.value.trim());
    });
    sortSelect.addEventListener('change', handleSort);
    compactToggle.addEventListener('change', handleCompactToggle);

    // ❌ REMOVE THIS LINE:
    // populateSortOptions();
}
// Populate sort select with dynamic options
function populateSortOptions() {
    const sortSelect = document.getElementById('sortSelect');
    sortSelect.innerHTML = '';

    // Base options
    const baseOptions = [
        { value: 'roll|asc', label: '🚩Sort by Roll (Ascending)🚩' },
        { value: 'roll|desc', label: 'Sort by Roll (Descending)' },
        { value: 'name|asc', label: 'Sort by Name (A-Z)' },
        { value: 'name|desc', label: 'Sort by Name (Z-A)' },
        { value: 'gpa|desc', label: 'Sort by GPA (with optional) (High to Low)' },
        { value: 'gpa|asc', label: 'Sort by GPA (with optional) (Low to High)' },
        { value: 'gpaWithoutAdditional|desc', label: 'Sort by GPA (High to Low)' },
        { value: 'gpaWithoutAdditional|asc', label: 'Sort by GPA (Low to High)' },
        { value: 'totalMark|desc', label: 'Sort by Total Marks (High to Low)' },
        { value: 'totalMark|asc', label: 'Sort by Total Marks (Low to High)' },
        { value: 'global|asc', label: '🚩Sort by Overall Rank (Best to Worst)🚩' },
        { value: 'global|desc', label: 'Sort by Overall Rank (Worst to Best)' },
        { value: 'section|asc', label: 'Sort by Section Rank (Best to Worst)' },
        { value: 'section|desc', label: 'Sort by Section Rank (Worst to Best)' }
    ];

    baseOptions.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.label;
        sortSelect.appendChild(option);
    });

    // Add subject options dynamically
    if (allSubjects.length > 0) {
        const divider = document.createElement('option');
        divider.disabled = true;
        divider.textContent = '───── Subjects ─────';
        sortSelect.appendChild(divider);

        allSubjects.forEach(subject => {
            const subjectName = subject.charAt(0).toUpperCase() + subject.slice(1);

            const optionDesc = document.createElement('option');
            optionDesc.value = `${subject}|desc`;
            optionDesc.textContent = `Sort by ${subjectName} (High to Low)`;
            sortSelect.appendChild(optionDesc);

            const optionAsc = document.createElement('option');
            optionAsc.value = `${subject}|asc`;
            optionAsc.textContent = `Sort by ${subjectName} (Low to High)`;
            sortSelect.appendChild(optionAsc);
        });
    }
}
// Handle search functionality


// Handle compact view toggle
function handleCompactToggle() {
    isCompactView = document.getElementById('compactToggle').checked;
    currentDetailSubject = null;
    currentDetailRow = null;

    handleSort();
}


// Create table header
function createTableHeader(header) {
    // Base columns
    const baseHeaders = [
        { key: 'toggle', label: '⚙️', width: '40px' },
        { key: 'roll', label: 'Roll' },
        { key: 'name', label: 'Name' },
        { key: 'global', label: 'Overall<br>Rank' },   // multiline
        { key: 'section', label: 'Section<br>Rank' }, // multiline
        { key: 'gpa', label: 'GPA' },
        { key: 'gpaWithOptional', label: 'GPA<br>(with optional)' },
        { key: 'totalMark', label: 'Total' }
    ];

    baseHeaders.forEach(col => {
        const th = document.createElement('th');
        th.innerHTML = col.label;  // ✅ use innerHTML instead of textContent
        if (col.width) th.style.width = col.width;
        th.style.textAlign = "center"; // looks cleaner
        header.appendChild(th);
    });


    // Subject columns
    allSubjects.forEach(subject => {
        const th = document.createElement('th');
        th.className = 'subject-header';
        th.onclick = () => toggleSubjectDetail(subject);

        const subjectName = subject.charAt(0).toUpperCase() + subject.slice(1);

        if (isCompactView && currentDetailSubject !== subject) {
            th.innerHTML = `${subjectName}<div class="detail-icon">+</div>`;
        } else if (!isCompactView || currentDetailSubject === subject) {
            th.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px; text-align: center;">
                    <div style="grid-column: 1/-1; border-bottom: 1px solid #2D3748; padding-bottom: 2px; margin-bottom: 2px;">${subjectName}</div>
                    <div>CQ</div><div>MCQ</div><div>Prac</div><div>Total</div>
                </div>
                ${currentDetailSubject === subject ? '<div class="detail-icon">-</div>' : ''}
            `;
        }

        header.appendChild(th);
    });

    // Transcript column
    const transcriptTh = document.createElement('th');
    transcriptTh.textContent = 'Transcript';
    header.appendChild(transcriptTh);
}
// Create table row
function createTableRow(body, student, index) {
    const tr = document.createElement('tr');
    const subNumber = 20;

    // Toggle column
    const toggleTd = document.createElement('td');
    toggleTd.innerHTML = `<span class="row-toggle" onclick="toggleRowDetail(${student.roll})">${currentDetailRow === student.roll ? '-' : '+'}</span>`;
    tr.appendChild(toggleTd);

    // Check if student is not qualified or absent
    const isNotQualified = student.status !== 'qualified';

    if (isNotQualified) {
        // Roll column
        const rollTd = document.createElement('td');
        rollTd.textContent = student.roll;
        tr.appendChild(rollTd);

        // Name column
        const nameTd = document.createElement('td');
        nameTd.textContent = student.name;
        tr.appendChild(nameTd);

        // Status message spanning all columns
        const statusTd = document.createElement('td');
        const statusText = student.status === 'absent' ? 'ABSENT' : 'NOT QUALIFIED';
        statusTd.textContent = statusText;
        statusTd.className = student.status === 'absent' ? 'absent' : 'not-qualified';
        statusTd.colSpan = allSubjects.length + 5;
        tr.appendChild(statusTd);

        // Transcript column
        const transcriptTd = document.createElement('td');
        if (student.url) {
            transcriptTd.innerHTML = `<a href="${student.url}" target="_blank" class="transcript-link">View</a>`;
        }
        tr.appendChild(transcriptTd);
    } else {
        // Roll
        const rollTd = document.createElement('td');
        rollTd.textContent = student.roll;
        tr.appendChild(rollTd);

        // Name
        const nameTd = document.createElement('td');
        nameTd.textContent = student.name;
        tr.appendChild(nameTd);

        // Global Ranking - apply color based on GPA
        const globalTd = document.createElement('td');
        globalTd.textContent = student.ranking.global;

        tr.appendChild(globalTd);
        // Section Ranking
        const sectionTd = document.createElement('td');

        if (student.ranking.section !== null && student.section) {
            sectionTd.textContent = `${student.ranking.section} (${student.section})`;
        } else {
            sectionTd.textContent = '-';
        }

        tr.appendChild(sectionTd);


        // GPA (Without Additional) - apply color based on value
        const gpaTd = document.createElement('td');
        const gpaVal = student.gpaWithoutAdditional !== null ? student.gpaWithoutAdditional : 0.00;
        gpaTd.textContent = gpaVal.toFixed(2);
        if (gpaVal === 0.00) {
            gpaTd.classList.add('text-danger');
        } else if (gpaVal === 5.00) {
            gpaTd.classList.add('text-good');
        }
        tr.appendChild(gpaTd);

        // GPA (With Optional)
        const gpaOptionalTd = document.createElement('td');
        const gpaOptVal = student.gpa !== null ? student.gpa : 0.00;
        gpaOptionalTd.textContent = gpaOptVal.toFixed(2);
        if (gpaOptVal === 0.00) {
            gpaOptionalTd.classList.add('text-danger');
        } else if (gpaOptVal === 5.00) {
            gpaOptionalTd.classList.add('text-good');
        }
        tr.appendChild(gpaOptionalTd);

        // Total Mark
        const totalMarkTd = document.createElement('td');
        totalMarkTd.textContent = student.totalMark.toFixed(0);
        tr.appendChild(totalMarkTd);

        // Subject columns
        allSubjects.forEach(subject => {
            const td = document.createElement('td');
            const subjectData = student.subjects[subject];

            if (!subjectData) {
                td.textContent = '-';
                td.style.color = '#666';
            } else if (isCompactView && currentDetailSubject !== subject && currentDetailRow !== student.roll) {
                // Compact view - show only termTotal
                td.textContent = subjectData.termTotal;

                // Apply color based on grade
                if (subjectData.grade === 'F') {
                    td.classList.add('text-danger');
                } else if (subjectData.grade === 'A+') {
                    td.classList.add('text-good');
                }
            } else {
                // Detail view - show all components
                const cqVal = subjectData.cq || '-';
                const mcqVal = subjectData.mcq || '-';
                const pracVal = subjectData.practical || '-';
                const totalVal = subjectData.termTotal || '-';

                // Determine colors for each component
                let cqClass = '';
                let mcqClass = '';
                let pracClass = '';
                let totalClass = '';

                // CQ coloring
                if (cqVal !== '-' && cqVal !== 'A') {
                    const cqNum = parseFloat(cqVal);
                    if (!isNaN(cqNum)) {
                        if (cqNum < subNumber / 2) {
                            cqClass = 'text-danger';
                        } else if (cqNum > subNumber * 0.8) {
                            cqClass = 'text-good';
                        }
                    }
                } else if (cqVal === 'A') {
                    cqClass = 'text-warning';
                }

                // MCQ coloring
                if (mcqVal !== '-') {
                    const mcqNum = parseFloat(mcqVal);
                    if (!isNaN(mcqNum)) {
                        if (mcqNum < (subNumber / 4) / 2) {
                            mcqClass = 'text-danger';
                        } else if (mcqNum > (subNumber / 4) * 0.8) {
                            mcqClass = 'text-good';
                        }
                    }
                }

                // Practical coloring
                if (pracVal !== '-') {
                    const pracNum = parseFloat(pracVal);
                    if (!isNaN(pracNum)) {
                        if (pracNum < (subNumber / 4) / 2) {
                            pracClass = 'text-danger';
                        } else if (pracNum > (subNumber / 4) * 0.8) {
                            pracClass = 'text-good';
                        }
                    }
                }

                // Total coloring based on grade
                if (subjectData.grade === 'F') {
                    totalClass = 'text-danger';
                } else if (subjectData.grade === 'A+') {
                    totalClass = 'text-good';
                }

                td.innerHTML = `
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; font-size: 10px;">
                        <div class="${cqClass}">${cqVal}</div>
                        <div class="${mcqClass}">${mcqVal}</div>
                        <div class="${pracClass}">${pracVal}</div>
                        <div class="${totalClass}">${totalVal}</div>
                    </div>
                `;
            }
            tr.appendChild(td);
        });

        // Transcript column
        const transcriptTd = document.createElement('td');
        if (student.url) {
            transcriptTd.innerHTML = `<a href="${student.url}" target="_blank" class="transcript-link">View</a>`;
        }
        tr.appendChild(transcriptTd);
    }

    body.appendChild(tr);
}

// Create empty row for padding
function createEmptyRow(body, index) {
    const tr = document.createElement('tr');
    const totalColumns = 8 + allSubjects.length + 1; // base columns (now 8) + subjects + transcript

    for (let i = 0; i < totalColumns; i++) {
        const td = document.createElement('td');
        td.innerHTML = '&nbsp;';
        td.style.height = '35px';
        tr.appendChild(td);
    }

    body.appendChild(tr);
}

// Toggle subject detail view
function toggleSubjectDetail(subject) {
    if (currentDetailSubject === subject) {
        currentDetailSubject = null;
    } else {
        currentDetailSubject = subject;
        currentDetailRow = null; // Reset row detail when subject detail is toggled
    }

    handleSort();
}

// Toggle row detail view
function toggleRowDetail(roll) {
    if (currentDetailRow === roll) {
        currentDetailRow = null;
    } else {
        currentDetailRow = roll;
        currentDetailSubject = null; // Reset subject detail when row detail is toggled
    }

    handleSort();
}

// Helper to select which GPA to use for analytics (for easy reversibility)
function getGpaForAnalytics(student) {
    // CURRENT: use gpaWithoutAdditional
    // TO REVERSE: change to 'return student.gpa;'
    return student.gpaWithoutAdditional !== null ? student.gpaWithoutAdditional : 0.00;
}

// Utility functions for analytics
function qualifiedCounter() {
    return Object.values(cleanData).filter(student => student.status === 'qualified').length;
}

function gradeCounter(subject, grade) {
    return Object.values(cleanData).filter(student =>
        student.status === 'qualified' &&
        student.subjects[subject] &&
        student.subjects[subject].grade === grade
    ).length;
}

// Count overall grades (A+, A, A-, …, F)
function gradeCounterOverall(grade) {
    return Object.values(cleanData).filter(student => {
        if (student.status !== "qualified") return false;
        return gpaToGrade(getGpaForAnalytics(student)) === grade;
    }).length;
}
function studentsQualifiedSubjectCounter(subject) {
    qualified1 = Object.values(cleanData).filter(student =>
        student.status === 'qualified' || student.status === 'absent'
    );
    return Object.values(qualified1).filter(student =>
        student.subjects[subject]
    ).length;
}

function studentsAttendedSubjectCounter(subject) {
    return Object.values(cleanData).filter(student =>
        student.status === 'qualified' &&
        student.subjects[subject]
    ).length;
}



function studentsAttendedExamCounter() {
    return qualifiedCounter();
}
function getOptionalSubjects(student) {
    if (!student.optionalSubject) return [];

    const opt = student.optionalSubject.toLowerCase();

    if (opt === "biology") {
        // Biology optional → both Botany & Zoology
        return Object.keys(student.subjects).filter(sub =>
            sub.toLowerCase().includes("botany") ||
            sub.toLowerCase().includes("zoology")
        );
    }

    // Otherwise → the given subject itself
    return Object.keys(student.subjects).filter(sub =>
        sub.toLowerCase().includes(opt)
    );
}
function totalFailedCounter(student) {
    if (student.status !== "qualified") return 0;

    const optionalSubjects = getOptionalSubjects(student);

    return Object.entries(student.subjects)
        .filter(([subjectName, subject]) => {
            return subject.grade === "F" && !optionalSubjects.includes(subjectName);
        })
        .length;
}

// Count how many failed in exactly N subjects (ignoring optional)
function failedCounter(failCount) {
    return Object.values(cleanData).filter(student => {
        if (student.status !== "qualified") return false;
        return totalFailedCounter(student) === failCount;
    }).length;
}


function gpaToGrade(gpa) {
    if (gpa >= 5.0) return 'A+';
    if (gpa >= 4.0) return 'A';
    if (gpa >= 3.5) return 'A-';
    if (gpa >= 3.0) return 'B';
    if (gpa >= 2.0) return 'C';
    if (gpa >= 1.0) return 'D';
    return 'F';
}

// Render section summary table
// Render section summary table
// Render section summary table
function renderSectionSummary() {
    const tbody = document.getElementById('sectionSummaryBody');
    const summarySection = document.querySelector('.summary-section');
    tbody.innerHTML = '';

    const allStudents = Object.values(cleanData);

    function buildRow(label, students) {
        const qualified = students.filter(s => s.status === 'qualified' || s.status === 'absent');
        const attended = students.filter(s => s.status === 'qualified');
        const passed = attended.filter(s => gpaToGrade(getGpaForAnalytics(s)) !== 'F');
        const failedOverall = attended.filter(s => gpaToGrade(getGpaForAnalytics(s)) === 'F');

        const tr = document.createElement('tr');

        // Label (Section or Overall)
        const sectionTd = document.createElement('td');
        sectionTd.textContent = label;
        sectionTd.style.fontWeight = 'bold';
        tr.appendChild(sectionTd);

        // --- Extra values ---
        const notQualified = students.length - qualified.length;
        const notAttended = qualified.length - attended.length;

        const stats = [
            students.length,        // Total
            qualified.length,       // Qualified
            notQualified,     // Not Qualified
            attended.length,        // Attended
            notAttended,      // Not Attended
            passed.length,          // Passed
            failedOverall.length,   // Failed
            attended.filter(s => gpaToGrade(getGpaForAnalytics(s)) === 'A+').length,
            attended.filter(s => gpaToGrade(getGpaForAnalytics(s)) === 'A').length,
            attended.filter(s => gpaToGrade(getGpaForAnalytics(s)) === 'A-').length,
            attended.filter(s => gpaToGrade(getGpaForAnalytics(s)) === 'B').length,
            attended.filter(s => gpaToGrade(getGpaForAnalytics(s)) === 'C').length,
            attended.filter(s => gpaToGrade(getGpaForAnalytics(s)) === 'D').length,
            attended.filter(s => totalFailedCounter(s) === 1).length,
            attended.filter(s => totalFailedCounter(s) === 2).length,
            attended.filter(s => totalFailedCounter(s) === 3).length,
            attended.filter(s => totalFailedCounter(s) >= 4).length
        ];

        stats.forEach((stat, index) => {
            const td = document.createElement('td');

            const numberDiv = document.createElement('div');
            numberDiv.textContent = stat;

            // --- Special yellow style for not qualified & not attended ---
            if (index === 2 || index === 4) {
                numberDiv.style.color = "var(--highlight-warning)"; // yellow background       // black text
                numberDiv.style.fontWeight = "bold";
                numberDiv.style.padding = "2px 6px";
                numberDiv.style.borderRadius = "6px";
            }

            td.appendChild(numberDiv);

            // Percentages (skip for Section, Total, Qualified, NotQ, NotA)
            if (index > 4 && typeof stat === "number" && attended.length > 0) {
                let percentage = ((stat / attended.length) * 100).toFixed(1);

                const percentDiv = document.createElement('div');
                percentDiv.textContent = `${percentage}%`;

                percentDiv.style.display = "inline-block";
                percentDiv.style.marginTop = "2px";
                percentDiv.style.padding = "2px 6px";
                percentDiv.style.fontSize = "11px";
                percentDiv.style.borderRadius = "10px";

                if ([5, 7, 8, 9, 10, 11, 12].includes(index)) {
                    percentDiv.style.background = "#0c472aff";
                    percentDiv.style.color = "#abffca";
                } else if ([6, 13, 14, 15, 16].includes(index)) {
                    percentDiv.style.background = "#7a0c0cff";
                    percentDiv.style.color = "#ffb3b3";
                }

                td.appendChild(percentDiv);
            }

            tr.appendChild(td);
        });

        return tr;
    }

    // Always Overall row
    tbody.appendChild(buildRow("Overall", allStudents));

    // Section rows
    const sections = [...new Set(allStudents
        .map(s => s.section)
        .filter(sec => sec && sec.trim() !== '')
    )];

    if (sections.length === 0) {
        summarySection.style.display = 'block';
        return;
    }

    sections.forEach(section => {
        const sectionStudents = allStudents.filter(student => student.section === section);
        tbody.appendChild(buildRow(section, sectionStudents));
    });

    summarySection.style.display = 'block';
}





// Render subject cards
function renderSubjectCards() {
    const container = document.getElementById('subjectCards');
    container.innerHTML = '';

    allSubjects.forEach(subject => {
        const qualified = studentsQualifiedSubjectCounter(subject)
        const total = studentsAttendedSubjectCounter(subject);
        const passed = Object.values(cleanData).filter(student =>
            student.status === 'qualified' &&
            student.subjects[subject] &&
            student.subjects[subject].grade !== 'F'
        ).length;

        const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;

        const card = document.createElement('div');
        card.className = 'subject-card';

        const subjectName = subject.charAt(0).toUpperCase() + subject.slice(1);

        card.innerHTML = `
            <div class="card-header">
                <div class="card-title">${subjectName}</div>
                <div class="pass-rate">${passRate}%</div>
            </div>
            <div class="card-body">
            <div class="stat-row">
            <span class="stat-label">Qualified:</span>
            <span class="stat-value">${qualified}</span>
        </div>
                <div class="stat-row">
                    <span class="stat-label">Attended:</span>
                    <span class="stat-value">${total}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Passed:</span>
                    <span class="stat-value">${passed}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Failed:</span>
                    <span class="stat-value">${total - passed}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">A+:</span>
                    <span class="stat-value">${gradeCounter(subject, 'A+')}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">A:</span>
                    <span class="stat-value">${gradeCounter(subject, 'A')}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">A-:</span>
                    <span class="stat-value">${gradeCounter(subject, 'A-')}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">B:</span>
                    <span class="stat-value">${gradeCounter(subject, 'B')}</span>
                </div>
            </div>
        `;

        container.appendChild(card);
    });
}
