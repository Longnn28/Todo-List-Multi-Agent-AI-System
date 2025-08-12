"""
Analytics helper functions for todo data analysis.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from src.config.database import TodoItem
from .database_helpers import get_completion_percentage, safe_average
from .date_helpers import get_weekday_name, get_hour_range_string
from .logger import logger


def analyze_productivity(db: Session, start_date: datetime, end_date: datetime, userId: int,
                      priority_filter: Optional[str] = None) -> str:
    """Analyze productivity metrics and patterns."""
    logger.info(f"Analyzing productivity from {start_date} to {end_date}, priority filter: {priority_filter}, userId: {userId}")
    
    # Total tasks created vs completed
    query = db.query(TodoItem).filter(TodoItem.createdAt >= start_date)
    if priority_filter:
        query = query.filter(TodoItem.priority == priority_filter)
    query = query.filter(TodoItem.userId == userId)
    
    total_tasks = query.count()
    completed_tasks = query.filter(TodoItem.status == 'done').count()
    
    # Tasks by priority
    priority_query = db.query(
        TodoItem.priority,
        func.count(TodoItem.id).label('total'),
        func.sum(case((TodoItem.status == 'done', 1), else_=0)).label('completed')
    ).filter(TodoItem.createdAt >= start_date)
    priority_query = priority_query.filter(TodoItem.userId == userId)
    
    priority_stats = priority_query.group_by(TodoItem.priority).all()
    
    # Overdue tasks
    overdue_query = db.query(TodoItem).filter(
        and_(
            TodoItem.deadline < datetime.now(),
            TodoItem.status != 'done',
            TodoItem.createdAt >= start_date
        )
    )
    overdue_query = overdue_query.filter(TodoItem.userId == userId)
    
    overdue_tasks = overdue_query.count()
    
    # Average completion time for completed tasks
    completed_query = db.query(TodoItem).filter(
        and_(
            TodoItem.status == 'done',
            TodoItem.createdAt >= start_date,
            TodoItem.updatedAt.isnot(None)
        )
    )
    completed_query = completed_query.filter(TodoItem.userId == userId)
    
    completed_with_dates = completed_query.all()
    
    completion_times = []
    for task in completed_with_dates:
        if task.updatedAt and task.createdAt:
            completion_time = (task.updatedAt - task.createdAt).total_seconds() / 3600  # hours
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
    
    logger.debug(f"Productivity analysis completed. Total tasks: {total_tasks}, Completed: {completed_tasks}")
    return result


def analyze_patterns(db: Session, start_date: datetime, end_date: datetime, userId: int,
                   priority_filter: Optional[str] = None) -> str:
    """Analyze behavioral patterns in task management."""
    
    # Creation patterns by day of week
    weekday_query = db.query(
        func.extract('dow', TodoItem.createdAt).label('weekday'),
        func.count(TodoItem.id).label('count')
    ).filter(TodoItem.createdAt >= start_date)
    weekday_query = weekday_query.filter(TodoItem.userId == userId)
    
    tasks_by_weekday = weekday_query.group_by('weekday').all()
    
    # Creation patterns by hour
    hour_query = db.query(
        func.extract('hour', TodoItem.createdAt).label('hour'),
        func.count(TodoItem.id).label('count')
    ).filter(TodoItem.createdAt >= start_date)
    hour_query = hour_query.filter(TodoItem.userId == userId)
    
    tasks_by_hour = hour_query.group_by('hour').all()
    
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


def analyze_completion_rate(db: Session, start_date: datetime, end_date: datetime, userId: int,
                        priority_filter: Optional[str] = None) -> str:
    """Analyze task completion rates and trends."""
    
    # Weekly completion trends
    weekly_stats = []
    current_date = start_date
    
    while current_date < end_date:
        week_end = min(current_date + timedelta(days=7), end_date)
        
        week_query = db.query(TodoItem).filter(
            and_(
                TodoItem.createdAt >= current_date,
                TodoItem.createdAt < week_end
            )
        )
        
        if priority_filter:
            week_query = week_query.filter(TodoItem.priority == priority_filter)
        
        week_query = week_query.filter(TodoItem.userId == userId)
        
        total = week_query.count()
        completed = week_query.filter(TodoItem.status == 'done').count()
        
        weekly_stats.append({
            'week_start': current_date.strftime('%m/%d'),
            'total': total,
            'completed': completed,
            'rate': get_completion_percentage(completed, total)
        })
        
        current_date = week_end
    
    # Completion rate by priority
    priority_query = db.query(
        TodoItem.priority,
        func.count(TodoItem.id).label('total'),
        func.sum(case((TodoItem.status == 'done', 1), else_=0)).label('completed')
    ).filter(TodoItem.createdAt >= start_date)
    priority_query = priority_query.filter(TodoItem.userId == userId)
    
    priority_completion = priority_query.group_by(TodoItem.priority).all()
    
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


def analyze_workload(db: Session, start_date: datetime, end_date: datetime, userId: int,
                  priority_filter: Optional[str] = None) -> str:
    """Analyze workload distribution and balance."""
    
    # Daily task creation
    daily_query = db.query(
        func.date(TodoItem.createdAt).label('date'),
        func.count(TodoItem.id).label('count')
    ).filter(TodoItem.createdAt >= start_date)
    daily_query = daily_query.filter(TodoItem.userId == userId)
    
    daily_creation = daily_query.group_by('date').order_by('date').all()
    
    # Pending tasks accumulation
    pending_query = db.query(
        TodoItem.priority,
        func.count(TodoItem.id).label('count')
    ).filter(
        and_(
            TodoItem.status == 'pending',
            TodoItem.createdAt >= start_date
        )
    )
    pending_query = pending_query.filter(TodoItem.userId == userId)
    
    pending_by_priority = pending_query.group_by(TodoItem.priority).all()
    
    # Tasks with due dates
    due_date_query = db.query(TodoItem).filter(
        and_(
            TodoItem.deadline.isnot(None),
            TodoItem.createdAt >= start_date
        )
    )
    due_date_query = due_date_query.filter(TodoItem.userId == userId)
    
    tasks_with_due_dates = due_date_query.count()
    
    # Total tasks
    total_query = db.query(TodoItem).filter(TodoItem.createdAt >= start_date)
    total_query = total_query.filter(TodoItem.userId == userId)
    
    total_tasks = total_query.count()
    
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


def get_analytics_summary(db: Session, start_date: datetime, end_date: datetime, userId: int) -> Dict[str, Any]:
    """
    Get summary analytics data for dashboard or quick overview.
    
    Returns:
        Dictionary with key metrics
    """
    logger.info(f"Generating analytics summary from {start_date} to {end_date}, userId: {userId}")
    
    # Total tasks
    total_query = db.query(TodoItem).filter(TodoItem.createdAt >= start_date)
    total_query = total_query.filter(TodoItem.userId == userId)
    total_tasks = total_query.count()
    
    # Completed tasks
    completed_query = db.query(TodoItem).filter(
        and_(TodoItem.createdAt >= start_date, TodoItem.status == 'done')
    )
    completed_query = completed_query.filter(TodoItem.userId == userId)
    completed_tasks = completed_query.count()
    
    # Pending tasks
    pending_query = db.query(TodoItem).filter(
        and_(TodoItem.createdAt >= start_date, TodoItem.status == 'pending')
    )
    pending_query = pending_query.filter(TodoItem.userId == userId)
    pending_tasks = pending_query.count()
    
    completion_rate = get_completion_percentage(completed_tasks, total_tasks)
    
    # High priority pending tasks
    high_priority_query = db.query(TodoItem).filter(
        and_(
            TodoItem.createdAt >= start_date,
            TodoItem.status == 'pending',
            TodoItem.priority == "high"
        )
    )
    high_priority_query = high_priority_query.filter(TodoItem.userId == userId)
    high_priority_pending = high_priority_query.count()
    
    # Overdue tasks
    overdue_query = db.query(TodoItem).filter(
        and_(
            TodoItem.deadline < datetime.now(),
            TodoItem.status == 'pending',
            TodoItem.createdAt >= start_date
        )
    )
    overdue_query = overdue_query.filter(TodoItem.userId == userId)
    overdue_tasks = overdue_query.count()
    
    result = {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "completion_rate": completion_rate,
        "high_priority_pending": high_priority_pending,
        "overdue_tasks": overdue_tasks,
        "analysis_period_days": (end_date - start_date).days
    }
    
    logger.debug(f"Analytics summary generated: {result}")
    return result
