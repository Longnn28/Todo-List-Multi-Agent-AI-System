"""
Templates for analytics functions.
"""

# Template for productivity analysis
PRODUCTIVITY_TEMPLATE = """PHÂN TÍCH HIỆU SUẤT CÔNG VIỆC ({days} ngày)

TỔNG QUAN:
• Tổng số task: {total_tasks}
• Đã hoàn thành: {completed_tasks} ({completion_percentage:.1f}%)
• Còn lại: {remaining_tasks}
• Quá hạn: {overdue_tasks}

PHÂN TÍCH THEO ĐỘ ƯU TIÊN:
{priority_stats}

THỜI GIAN HOÀN THÀNH TRUNG BÌNH: {avg_completion_time:.1f} giờ

NHẬN XÉT VÀ GỢI Ý:
{insights}"""

# Template for pattern analysis
PATTERNS_TEMPLATE = """PHÂN TÍCH PATTERN CÔNG VIỆC ({days} ngày)

PATTERN TẠO TASK THEO NGÀY TRONG TUẦN:
{weekday_patterns}

PATTERN TẠO TASK THEO GIỜ:
{hourly_patterns}

GIỜ VÀNG TẠO TASK: {peak_hours}

NHẬN XÉT PATTERN:
{pattern_insights}"""

# Template for completion rate analysis
COMPLETION_RATE_TEMPLATE = """PHÂN TÍCH TỶ LỆ HOÀN THÀNH ({days} ngày)

XU HƯỚNG THEO TUẦN:
{weekly_trends}

TỶ LỆ HOÀN THÀNH THEO ƯU TIÊN:
{priority_completion}

{trend_analysis}"""

# Template for workload analysis
WORKLOAD_TEMPLATE = """PHÂN TÍCH KHỐI LƯỢNG CÔNG VIỆC ({days} ngày)

PHÂN BỐ TẠO TASK HÀNG NGÀY:
{daily_distribution}

CÔNG VIỆC ĐANG CHỜ XỬ LÝ:
{pending_tasks}

TASK CÓ DEADLINE: {tasks_with_due_dates}/{total_tasks} ({deadline_percentage:.1f}%)

ĐÁNH GIÁ KHỐI LƯỢNG CÔNG VIỆC:
{workload_insights}"""
