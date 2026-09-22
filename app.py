from flask import Flask, render_template, request
import pandas as pd
import io

app = Flask(__name__)

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
                        tables[topic_name] = df[valid_cols].head(10).to_html(
                            classes='table table-striped table-hover table-bordered table-sm responsive-table',
                            index=False
                        )
                    else:
                        tables[topic_name] = "<div class='alert alert-warning'>ไม่พบคอลัมน์ที่ระบุในชุดข้อมูล</div>"
            except Exception as e:
                error = f"เกิดข้อผิดพลาดในการเปิดไฟล์: {str(e)}"
    
    return render_template('index.html', tables=tables, error=error)

if __name__ == '__main__':
    app.run(debug=True)