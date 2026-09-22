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
    <title>HR Data Viewer - Full Data</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .table-container {
            max-height: 75vh;
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
    </style>
</head>
<body class="bg-light">
    <div class="container-fluid px-4 py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="text-primary fw-bold mb-0">📊 ระบบแสดงผลข้อมูลพนักงาน (HR Data Viewer)</h2>
            {% if tables %}
                <a href="/" class="btn btn-outline-danger">🗑️ ล้างข้อมูล / อัปโหลดใหม่</a>
            {% endif %}
        </div>
        
        <div class="card mb-4 shadow-sm">
            <div class="card-body">
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
</body>
</html>"""

TOPICS = {
    "1. ข้อมูลส่วนบุคคลและอัตลักษณ์": [
        'EmpID', 'Employee_Name', 'DOB', 'Sex', 'GenderID', 
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
