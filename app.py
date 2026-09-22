import io
from flask import Flask, render_template_string, request
import pandas as pd

app = Flask(__name__)

# ตั้งค่า Pandas ให้แสดงผลข้อมูลแบบเต็ม 100% ไม่ตัดคำ ไม่ซ่อนแถว/คอลัมน์
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HR Data Viewer - Full Filter with Age</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .table-container {
            max-height: 65vh;
            overflow: auto;
            border: 1px solid #dee2e6;
        }
        .table thead th {
            position: sticky;
            top: 0;
            background-color: #212529 !important;
            color: #ffffff !important;
            z-index: 2;
            white-space: nowrap;
        }
        .table td {
            white-space: nowrap;
        }
        .filter-card {
            background-color: #f8f9fa;
            border-left: 4px solid #0d6efd;
        }
    </style>
</head>
<body class="bg-light">
    <div class="container-fluid px-4 py-4">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="text-primary fw-bold mb-0">📊 ระบบแสดงผลและกรองข้อมูลพนักงาน (HR Data Viewer)</h2>
            {% if tables %}
                <a href="/" class="btn btn-outline-danger">🗑️ ล้างข้อมูล / อัปโหลดใหม่</a>
            {% endif %}
        </div>
        
        <div class="card mb-3 shadow-sm">
            <div class="card-body py-3">
                <form method="POST" enctype="multipart/form-data" class="row g-3 align-items-center">
                    <div class="col-md-9">
                        <input type="file" name="file" class="form-control" accept=".txt,.csv" required>
                    </div>
                    <div class="col-md-3 d-flex gap-2">
                        <button type="submit" class="btn btn-primary w-100">อัปโหลดและแสดงผลทั้งหมด</button>
                        {% if tables %}
                            <a href="/" class="btn btn-secondary w-50">รีเซ็ต</a>
                        {% endif %}
                    </div>
                </form>
            </div>
        </div>

        {% if error %}
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                {{ error }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        {% endif %}

        {% if tables %}
            <!-- แผงค้นหาและตัวกรองข้อมูล -->
            <div class="card mb-3 shadow-sm filter-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="fw-bold text-dark mb-0">🎯 ระบบค้นหาและตัวกรองข้อมูล (Filter)</h5>
                        <div class="d-flex align-items-center gap-3">
                            <span id="rowCountInfo" class="badge bg-primary fs-6 fw-normal">กำลังคำนวณ...</span>
                            <button class="btn btn-sm btn-outline-secondary" type="button" id="resetFiltersBtn">🔄 ล้างตัวกรองทั้งหมด</button>
                        </div>
                    </div>

                    <!-- ช่องค้นหาคำรวม -->
                    <div class="mb-3">
                        <div class="input-group">
                            <span class="input-group-text bg-dark text-white">🔍 ค้นหารวมทุกคอลัมน์</span>
                            <input type="text" id="searchInput" class="form-control" placeholder="พิมพ์คำที่ต้องการค้นหาทั่วทั้งตาราง...">
                        </div>
                    </div>

                    <!-- พื้นที่สร้างตัวกรองแยกตามคอลัมน์อัตโนมัติ -->
                    <div class="border-top pt-3">
                        <div class="fw-bold small text-muted mb-2">⚙️ ตัวกรองแยกตามคอลัมน์ (Filter by Column):</div>
                        <div id="dynamicFilters" class="row g-2">
                            <!-- JS จะสร้าง Dropdown / Input ของแต่ละคอลัมน์ให้ที่นี่ -->
                        </div>
                    </div>
                </div>
            </div>

            <ul class="nav nav-tabs" id="dataTabs" role="tablist">
                {% for topic in tables.keys() %}
                    <li class="nav-item" role="presentation">
                        <button class="nav-link {% if loop.first %}active{% endif %}" id="tab-{{ loop.index }}" data-bs-toggle="tab" data-bs-target="#content-{{ loop.index }}" type="button" role="tab">{{ topic }}</button>
                    </li>
                {% endfor %}
            </ul>
            <div class="tab-content bg-white p-3 border border-top-0 rounded-bottom shadow-sm" id="dataTabsContent">
                {% for topic, table_html in tables.items() %}
                    <div class="tab-pane fade {% if loop.first %}show active{% endif %}" id="content-{{ loop.index }}" role="tabpanel">
                        <div class="table-container">
                            {{ table_html | safe }}
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const searchInput = document.getElementById('searchInput');
            const resetBtn = document.getElementById('resetFiltersBtn');
            const dynamicFiltersContainer = document.getElementById('dynamicFilters');

            function buildColumnFilters() {
                if (!dynamicFiltersContainer) return;
                dynamicFiltersContainer.innerHTML = '';

                const activeTab = document.querySelector('.tab-pane.active');
                if (!activeTab) return;

                const table = activeTab.querySelector('table');
                if (!table) return;

                const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
                const tbody = table.querySelector('tbody');
                if (!tbody) return;

                const rows = Array.from(tbody.querySelectorAll('tr'));

                headers.forEach((header, colIndex) => {
                    const uniqueValues = new Set();
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells[colIndex]) {
                            const val = cells[colIndex].textContent.trim();
                            if (val !== '') uniqueValues.add(val);
                        }
                    });

                    const sortedVals = Array.from(uniqueValues).sort((a, b) => {
                        const numA = parseFloat(a), numB = parseFloat(b);
                        if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
                        return a.localeCompare(b, 'th');
                    });

                    const colDiv = document.createElement('div');
                    colDiv.className = 'col-md-3 col-sm-6';

                    const label = document.createElement('label');
                    label.className = 'form-label small fw-bold text-truncate w-100 mb-1';
                    label.title = header;
                    label.textContent = header;

                    let inputEl;
                    if (sortedVals.length > 0 && sortedVals.length <= 150) {
                        inputEl = document.createElement('select');
                        inputEl.className = 'form-select form-select-sm col-filter';
                        inputEl.dataset.colIndex = colIndex;

                        const defaultOpt = document.createElement('option');
                        defaultOpt.value = '';
                        defaultOpt.textContent = `-- ทั้งหมด (${sortedVals.length}) --`;
                        inputEl.appendChild(defaultOpt);

                        sortedVals.forEach(v => {
                            const opt = document.createElement('option');
                            opt.value = v;
                            opt.textContent = v;
                            inputEl.appendChild(opt);
                        });
                    } else {
                        inputEl = document.createElement('input');
                        inputEl.type = 'text';
                        inputEl.className = 'form-control form-control-sm col-filter';
                        inputEl.placeholder = `ค้น ${header}...`;
                        inputEl.dataset.colIndex = colIndex;
                    }

                    inputEl.addEventListener('change', applyAllFilters);
                    inputEl.addEventListener('input', applyAllFilters);

                    colDiv.appendChild(label);
                    colDiv.appendChild(inputEl);
                    dynamicFiltersContainer.appendChild(colDiv);
                });

                applyAllFilters();
            }

            function applyAllFilters() {
                const activeTab = document.querySelector('.tab-pane.active');
                if (!activeTab) return;

                const table = activeTab.querySelector('table');
                if (!table) return;

                const globalFilter = (searchInput?.value || '').toLowerCase().trim();
                const colFilters = Array.from(document.querySelectorAll('.col-filter'));

                const rows = Array.from(table.querySelectorAll('tbody tr'));
                let visibleCount = 0;

                rows.forEach(row => {
                    const cells = Array.from(row.querySelectorAll('td'));
                    const rowText = row.textContent.toLowerCase();

                    let matchGlobal = true;
                    if (globalFilter && !rowText.includes(globalFilter)) {
                        matchGlobal = false;
                    }

                    let matchCols = true;
                    if (matchGlobal) {
                        for (let filterEl of colFilters) {
                            const colIdx = parseInt(filterEl.dataset.colIndex);
                            const filterVal = filterEl.value.trim().toLowerCase();
                            
                            if (filterVal !== '') {
                                const cellVal = (cells[colIdx]?.textContent || '').trim().toLowerCase();
                                if (filterEl.tagName === 'SELECT') {
                                    if (cellVal !== filterVal) {
                                        matchCols = false;
                                        break;
                                    }
                                } else {
                                    if (!cellVal.includes(filterVal)) {
                                        matchCols = false;
                                        break;
                                    }
                                }
                            }
                        }
                    }

                    const isVisible = matchGlobal && matchCols;
                    row.style.display = isVisible ? '' : 'none';
                    if (isVisible) visibleCount++;
                });

                const infoEl = document.getElementById('rowCountInfo');
                if (infoEl) {
                    infoEl.textContent = `แสดง ${visibleCount.toLocaleString()} จาก ${rows.length.toLocaleString()} รายการ`;
                }
            }

            if (searchInput) {
                searchInput.addEventListener('keyup', applyAllFilters);
                searchInput.addEventListener('input', applyAllFilters);
            }

            if (resetBtn) {
                resetBtn.addEventListener('click', function() {
                    if (searchInput) searchInput.value = '';
                    document.querySelectorAll('.col-filter').forEach(f => f.value = '');
                    applyAllFilters();
                });
            }

            const tabElList = document.querySelectorAll('button[data-bs-toggle="tab"]');
            tabElList.forEach(tabEl => {
                tabEl.addEventListener('shown.bs.tab', function() {
                    buildColumnFilters();
                });
            });

            buildColumnFilters();
        });
    </script>
</body>
</html>"""

TOPICS = {
    "1. ข้อมูลส่วนบุคคลและอัตลักษณ์": [
        'EmpID', 'Employee_Name', 'DOB', 'Age', 'Sex', 'GenderID', 
        'MarriedID', 'MaritalStatusID', 'MaritalDesc', 
        'CitizenDesc', 'HispanicLatino', 'RaceDesc'
    ],
    "2. ตำแหน่งงาน แผนก และสายการบังคับบัญชา": [
        'EmpID', 'Employee_Name', 'Position', 'PositionID', 
        'Department', 'DeptID', 'ManagerName', 'ManagerID'
    ],
    "3. สถานะและประวัติการจ้างงาน": [
        'EmpID', 'Employee_Name', 'EmploymentStatus', 'EmpStatusID', 
        'DateofHire', 'DateofTermination', 'TermReason', 'Termd'
    ],
    "4. อัตราตอบแทนและผลการปฏิบัติงาน": [
        'EmpID', 'Employee_Name', 'PayRate', 'PerformanceScore', 'PerfScoreID', 
        'EngagementSurvey', 'EmpSatisfaction', 'SpecialProjectsCount', 
        'LastPerformanceReview_Date', 'DaysLateLast30'
    ],
    "5. ข้อมูลที่อยู่และช่องทางการสรรหา": [
        'EmpID', 'Employee_Name', 'State', 'Zip', 
        'RecruitmentSource', 'FromDiversityJobFairID', 'Original DS'
    ]
}

@app.route('/', methods=['GET', 'POST'])
def index():
    tables = {}
    error = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            try:
                content = file.stream.read().decode('utf-8', errors='ignore')
                df = pd.read_csv(io.StringIO(content), sep=None, engine='python')
                
                # คำนวณอายุจาก DOB ถ้ามี DOB แต่ไม่มี Age
                if 'DOB' in df.columns and 'Age' not in df.columns:
                    try:
                        dob_dt = pd.to_datetime(df['DOB'], errors='coerce')
                        now = pd.Timestamp.now()
                        # แก้ไขปีถ้าถูกตีความเกินปีปัจจุบัน (เช่น ปี ค.ศ. แบบ 2 หลัก)
                        dob_dt = dob_dt.apply(lambda d: d.replace(year=d.year - 100) if pd.notnull(d) and d > now else d)
                        ages = (now - dob_dt).dt.days // 365.25
                        df['Age'] = ages.apply(lambda x: int(x) if pd.notnull(x) and x >= 0 else "-")
                    except Exception:
                        pass

                for topic_name, cols in TOPICS.items():
                    valid_cols = [c for c in cols if c in df.columns]
                    if valid_cols:
                        sub_df = df[valid_cols].copy()
                        # แทรกคอลัมน์ "ลำดับ" เริ่มต้นที่ 1 ไว้ที่ตำแหน่งแรกสุด
                        sub_df.insert(0, 'ลำดับ', range(1, len(sub_df) + 1))
                        
                        tables[topic_name] = sub_df.to_html(
                            classes='table table-striped table-hover table-bordered table-sm align-middle',
                            index=False,
                            max_rows=None,
                            max_cols=None
                        )
                    else:
                        tables[topic_name] = "<div class='alert alert-warning'>ไม่พบคอลัมน์ที่ระบุในชุดข้อมูล</div>"
            except Exception as e:
                error = f"เกิดข้อผิดพลาดในการเปิดไฟล์: {str(e)}"
    
    return render_template_string(HTML_TEMPLATE, tables=tables, error=error)

if __name__ == '__main__':
    app.run(debug=True)
