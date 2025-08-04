"""
Analytics helper functions for todo data analysis.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from config.database import TodoItem
from .database_helpers import safe_sum_boolean, get_completion_percentage, safe_average
from .date_helpers import get_weekday_name, get_hour_range_string


def analyze_productivity(db: Session, start_date: datetime, end_date: datetime, priority_filter: Optional[str] = None) -> str:
    """Analyze productivity metrics and patterns."""
    
    # Total tasks created vs completed
    query = db.query(TodoItem).filter(TodoItem.created_at >= start_date)
    if priority_filter:
        query = query.filter(TodoItem.priority == priority_filter)
    
    total_tasks = query.count()
    completed_tasks = query.filter(TodoItem.completed == True).count()
    
    # Tasks by priority
    priority_stats = db.query(
        TodoItem.priority,
        func.count(TodoItem.id).label('total'),
        safe_sum_boolean(TodoItem.completed).label('completed')
    ).filter(TodoItem.created_at >= start_date).group_by(TodoItem.priority).all()
    
    # Overdue tasks
    overdue_tasks = db.query(TodoItem).filter(
        and_(
            TodoItem.due_date < datetime.now(),
            TodoItem.completed == False,
            TodoItem.created_at >= start_date
        )
    ).count()
    
    # Average completion time for completed tasks
    completed_with_dates = db.query(TodoItem).filter(
        and_(
            TodoItem.completed == True,
            TodoItem.created_at >= start_date,
            TodoItem.updated_at.isnot(None)
        )
    ).all()
    
    completion_times = []
    for task in completed_with_dates:
        if task.updated_at and task.created_at:
            completion_time = (task.updated_at - task.created_at).total_seconds() / 3600  # hours
            completion_times.append(completion_time)
    
    avg_completion_time = safe_average(completion_times)
    
    result = f"""📊 PHÂN TÍCH HIỆU SUẤT CÔNG VIỆC ({(end_date - start_date).days} ngày)

🎯 TỔNG QUAN:
• Tổng số task: {total_tasks}
• Đã hoàn thành: {completed_tasks} ({get_completion_percentage(completed_tasks, total_tasks):.1f}%)
• Còn lại: {total_tasks - completed_tasks}
• Quá hạn: {overdue_tasks}

⚡ PHÂN TÍCH THEO ĐỘ ƯU TIÊN:"""
    
    for priority, total, completed in priority_stats:
        completed = completed or 0
        completion_rate = get_completion_percentage(completed, total)
        result += f"\n• {priority.upper()}: {completed}/{total} ({completion_rate:.1f}%)"
    
    result += f"\n\n⏱️ THỜI GIAN HOÀN THÀNH TRUNG BÌNH: {avg_completion_time:.1f} giờ"
    
    # Productivity insights
    result += "\n\n💡 NHẬN XÉT VÀ GỢI Ý:"
    
    completion_rate = get_completion_percentage(completed_tasks, total_tasks)
    
    if completion_rate >= 80:
        result += "\n✅ Hiệu suất tuyệt vời! Bạn đang quản lý công việc rất tốt."
    elif completion_rate >= 60:
        result += "\n👍 Hiệu suất khá tốt, có thể cải thiện thêm một chút."
    else:
        result += "\n⚠️ Cần cải thiện hiệu suất. Hãy thử chia nhỏ task và ưu tiên công việc."
    
    if total_tasks > 0 and overdue_tasks > total_tasks * 0.2:
        result += "\n🚨 Có quá nhiều task quá hạn. Nên đặt deadline thực tế hơn."
    
    if avg_completion_time > 48:
        result += "\n⏰ Task mất quá nhiều thời gian. Hãy chia nhỏ công việc."
    
    return result


def analyze_patterns(db: Session, start_date: datetime, end_date: datetime, priority_filter: Optional[str] = None) -> str:
    """Analyze behavioral patterns in task management."""
    
    # Creation patterns by day of week
    tasks_by_weekday = db.query(
        func.extract('dow', TodoItem.created_at).label('weekday'),
        func.count(TodoItem.id).label('count')
    ).filter(TodoItem.created_at >= start_date).group_by('weekday').all()
    
    # Creation patterns by hour
    tasks_by_hour = db.query(
        func.extract('hour', TodoItem.created_at).label('hour'),
        func.count(TodoItem.id).label('count')
    ).filter(TodoItem.created_at >= start_date).group_by('hour').all()
    
    # Most common task patterns
    common_keywords = {}
    tasks = db.query(TodoItem).filter(TodoItem.created_at >= start_date).all()
    
    for task in tasks:
        words = task.title.lower().split()
        for word in words:
            if len(word) > 3:  # Ignore short words
                common_keywords[word] = common_keywords.get(word, 0) + 1
    
    # Sort by frequency
    top_keywords = sorted(common_keywords.items(), key=lambda x: x[1], reverse=True)[:5]
    
    result = f"""🔍 PHÂN TÍCH PATTERN CÔNG VIỆC ({(end_date - start_date).days} ngày)

📅 PATTERN TẠO TASK THEO NGÀY TRONG TUẦN:"""
    
    weekday_data = {int(day): count for day, count in tasks_by_weekday}
    
    for i in range(7):
        count = weekday_data.get(i, 0)
        day_name = get_weekday_name(i)
        result += f"\n• {day_name}: {count} task"
    
    result += "\n\n🕐 PATTERN TẠO TASK THEO GIỜ:"
    hour_data = {int(hour): count for hour, count in tasks_by_hour}
    
    peak_hours = []
    max_count = max(hour_data.values()) if hour_data else 0
    
    for hour in range(24):
        count = hour_data.get(hour, 0)
        if count > 0:
            hour_range = get_hour_range_string(hour)
            result += f"\n• {hour_range}: {count} task"
            if count >= max_count * 0.7:  # Peak hours
                peak_hours.append(f"{hour:02d}:00")
    
    result += f"\n\n🔥 GIỜ VÀNG TẠO TASK: {', '.join(peak_hours) if peak_hours else 'Không có pattern rõ ràng'}"
    
    result += "\n\n📝 TỪ KHÓA PHỔ BIẾN TRONG TASK:"
    for keyword, freq in top_keywords:
        result += f"\n• '{keyword}': {freq} lần"
    
    # Pattern insights
    result += "\n\n💡 NHẬN XÉT PATTERN:"
    
    # Find most productive day
    if weekday_data:
        most_productive_day = max(weekday_data.items(), key=lambda x: x[1])
        day_name = get_weekday_name(most_productive_day[0])
        result += f"\n📈 Ngày tạo task nhiều nhất: {day_name}"
    
    # Find peak hour
    if hour_data:
        peak_hour = max(hour_data.items(), key=lambda x: x[1])
        result += f"\n⏰ Giờ tạo task nhiều nhất: {peak_hour[0]:02d}:00"
    
    return result


def analyze_completion_rate(db: Session, start_date: datetime, end_date: datetime, priority_filter: Optional[str] = None) -> str:
    """Analyze task completion rates and trends."""
    
    # Weekly completion trends
    weekly_stats = []
    current_date = start_date
    
    while current_date < end_date:
        week_end = min(current_date + timedelta(days=7), end_date)
        
        week_query = db.query(TodoItem).filter(
            and_(
                TodoItem.created_at >= current_date,
                TodoItem.created_at < week_end
            )
        )
        
        if priority_filter:
            week_query = week_query.filter(TodoItem.priority == priority_filter)
        
        total = week_query.count()
        completed = week_query.filter(TodoItem.completed == True).count()
        
        weekly_stats.append({
            'week_start': current_date.strftime('%m/%d'),
            'total': total,
            'completed': completed,
            'rate': get_completion_percentage(completed, total)
        })
        
        current_date = week_end
    
    # Completion rate by priority
    priority_completion = db.query(
        TodoItem.priority,
        func.count(TodoItem.id).label('total'),
        safe_sum_boolean(TodoItem.completed).label('completed')
    ).filter(TodoItem.created_at >= start_date).group_by(TodoItem.priority).all()
    
    result = f"""📈 PHÂN TÍCH TỶ LỆ HOÀN THÀNH ({(end_date - start_date).days} ngày)

📊 XU HƯỚNG THEO TUẦN:"""
    
    for week in weekly_stats:
        result += f"\n• Tuần {week['week_start']}: {week['completed']}/{week['total']} ({week['rate']:.1f}%)"
    
    result += "\n\n🎯 TỶ LỆ HOÀN THÀNH THEO ƯU TIÊN:"
    
    for priority, total, completed in priority_completion:
        completed = completed or 0
        rate = get_completion_percentage(completed, total)
        result += f"\n• {priority.upper()}: {completed}/{total} ({rate:.1f}%)"
    
    # Trend analysis
    if len(weekly_stats) >= 2:
        recent_rate = weekly_stats[-1]['rate']
        previous_rate = weekly_stats[-2]['rate']
        trend = recent_rate - previous_rate
        
        result += f"\n\n📊 XU HƯỚNG GẦN ĐÂY:"
        if trend > 5:
            result += f"\n📈 Hiệu suất đang cải thiện (+{trend:.1f}%)"
        elif trend < -5:
            result += f"\n📉 Hiệu suất đang giảm ({trend:.1f}%)"
        else:
            result += f"\n➡️ Hiệu suất ổn định ({trend:+.1f}%)"
    
    return result


def analyze_workload(db: Session, start_date: datetime, end_date: datetime, priority_filter: Optional[str] = None) -> str:
    """Analyze workload distribution and balance."""
    
    # Daily task creation
    daily_creation = db.query(
        func.date(TodoItem.created_at).label('date'),
        func.count(TodoItem.id).label('count')
    ).filter(TodoItem.created_at >= start_date).group_by('date').order_by('date').all()
    
    # Pending tasks accumulation
    pending_by_priority = db.query(
        TodoItem.priority,
        func.count(TodoItem.id).label('count')
    ).filter(
        and_(
            TodoItem.completed == False,
            TodoItem.created_at >= start_date
        )
    ).group_by(TodoItem.priority).all()
    
    # Tasks with due dates
    tasks_with_due_dates = db.query(TodoItem).filter(
        and_(
            TodoItem.due_date.isnot(None),
            TodoItem.created_at >= start_date
        )
    ).count()
    
    total_tasks = db.query(TodoItem).filter(TodoItem.created_at >= start_date).count()
    
    result = f"""⚖️ PHÂN TÍCH KHỐI LƯỢNG CÔNG VIỆC ({(end_date - start_date).days} ngày)

📅 PHÂN BỐ TẠO TASK HÀNG NGÀY:"""
    
    creation_counts = [count for _, count in daily_creation]
    if creation_counts:
        avg_daily = safe_average(creation_counts)
        max_daily = max(creation_counts)
        result += f"\n• Trung bình: {avg_daily:.1f} task/ngày"
        result += f"\n• Cao nhất: {max_daily} task/ngày"
        
        # Show recent days
        result += "\n• 7 ngày gần nhất:"
        for date, count in daily_creation[-7:]:
            result += f"\n  - {date}: {count} task"
    
    result += f"\n\n📋 CÔNG VIỆC ĐANG PENDING:"
    pending_total = 0
    for priority, count in pending_by_priority:
        result += f"\n• {priority.upper()}: {count} task"
        pending_total += count
    
    result += f"\n• TỔNG: {pending_total} task"
    
    deadline_percentage = get_completion_percentage(tasks_with_due_dates, total_tasks)
    result += f"\n\n⏰ TASK CÓ DEADLINE: {tasks_with_due_dates}/{total_tasks} ({deadline_percentage:.1f}%)"
    
    # Workload insights
    result += "\n\n💡 ĐÁNH GIÁ KHỐI LƯỢNG CÔNG VIỆC:"
    
    if pending_total > 20:
        result += "\n🚨 Khối lượng công việc quá tải! Cần ưu tiên và loại bỏ task không cần thiết."
    elif pending_total > 10:
        result += "\n⚠️ Khối lượng công việc khá nhiều. Nên tập trung vào task ưu tiên cao."
    else:
        result += "\n✅ Khối lượng công việc hợp lý, có thể quản lý tốt."
    
    if creation_counts and max(creation_counts) > safe_average(creation_counts) * 2:
        result += "\n📊 Có ngày tạo quá nhiều task. Nên phân bổ đều hơn."
    
    if deadline_percentage < 30:
        result += "\n📅 Nên đặt deadline cho nhiều task hơn để quản lý thời gian tốt hơn."
    
    return result


def get_analytics_summary(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Get summary analytics data for dashboard or quick overview.
    
    Returns:
        Dictionary with key metrics
    """
    total_tasks = db.query(TodoItem).filter(TodoItem.created_at >= start_date).count()
    completed_tasks = db.query(TodoItem).filter(
        and_(TodoItem.created_at >= start_date, TodoItem.completed == True)
    ).count()
    
    pending_tasks = total_tasks - completed_tasks
    completion_rate = get_completion_percentage(completed_tasks, total_tasks)
    
    # High priority pending tasks
    high_priority_pending = db.query(TodoItem).filter(
        and_(
            TodoItem.created_at >= start_date,
            TodoItem.completed == False,
            TodoItem.priority == "high"
        )
    ).count()
    
    # Overdue tasks
    overdue_tasks = db.query(TodoItem).filter(
        and_(
            TodoItem.due_date < datetime.now(),
            TodoItem.completed == False,
            TodoItem.created_at >= start_date
        )
    ).count()
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "completion_rate": completion_rate,
        "high_priority_pending": high_priority_pending,
        "overdue_tasks": overdue_tasks,
        "analysis_period_days": (end_date - start_date).days
    }
