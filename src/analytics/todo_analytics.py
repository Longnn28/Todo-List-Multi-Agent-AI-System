from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from src.config.database import TodoItem
from src.utils.database_helpers import get_completion_percentage, safe_average
from src.utils.date_helpers import get_weekday_name, get_hour_range_string
from src.analytics.templates import (
    PRODUCTIVITY_TEMPLATE, 
    PATTERNS_TEMPLATE, 
    COMPLETION_RATE_TEMPLATE, 
    WORKLOAD_TEMPLATE
)


def analyze_productivity(db: Session, start_date: datetime, end_date: datetime, userId: int) -> str:
    """Analyze productivity metrics and patterns."""
    
    # Lấy dữ liệu phân tích
    data = _get_productivity_data(db, start_date, end_date, userId)
    
    # Định dạng dữ liệu theo template
    return _format_productivity_result(data, start_date, end_date)


def _get_productivity_data(db: Session, start_date: datetime, end_date: datetime, userId: int) -> Dict[str, Any]:
    """Extract productivity data from database."""
    # Total tasks created vs completed
    query = db.query(TodoItem).filter(TodoItem.createdAt >= start_date)
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
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks,
        "priority_stats": priority_stats,
        "avg_completion_time": avg_completion_time
    }


def _format_productivity_result(data: Dict[str, Any], start_date: datetime, end_date: datetime) -> str:
    """Format productivity data into readable text using template."""
    # Xây dựng phần priority stats
    priority_stats_text = ""
    for priority, total, completed in data["priority_stats"]:
        completed = completed or 0
        completion_rate = get_completion_percentage(completed, total)
        priority_stats_text += f"\n• {priority.upper()}: {completed}/{total} ({completion_rate:.1f}%)"
    
    # Xây dựng insights
    insights = []
    completion_rate = get_completion_percentage(data["completed_tasks"], data["total_tasks"])
    
    if completion_rate >= 80:
        insights.append("Hiệu suất tuyệt vời! Bạn đang quản lý công việc rất tốt.")
    elif completion_rate >= 60:
        insights.append("Hiệu suất khá tốt, có thể cải thiện thêm một chút.")
    else:
        insights.append("Cần cải thiện hiệu suất. Hãy thử chia nhỏ task và ưu tiên công việc.")
    
    if data["total_tasks"] > 0 and data["overdue_tasks"] > data["total_tasks"] * 0.2:
        insights.append("Có quá nhiều task quá hạn. Nên đặt deadline thực tế hơn.")
    
    if data["avg_completion_time"] > 48:
        insights.append("Task mất quá nhiều thời gian. Hãy chia nhỏ công việc.")
    
    # Áp dụng template
    return PRODUCTIVITY_TEMPLATE.format(
        days=(end_date - start_date).days,
        total_tasks=data["total_tasks"],
        completed_tasks=data["completed_tasks"],
        completion_percentage=get_completion_percentage(data["completed_tasks"], data["total_tasks"]),
        remaining_tasks=data["total_tasks"] - data["completed_tasks"],
        overdue_tasks=data["overdue_tasks"],
        priority_stats=priority_stats_text,
        avg_completion_time=data["avg_completion_time"],
        insights="\n".join(insights)
    )


def analyze_patterns(db: Session, start_date: datetime, end_date: datetime, userId: int) -> str:
    """Analyze behavioral patterns in task management."""
    
    # Lấy dữ liệu phân tích
    data = _get_patterns_data(db, start_date, end_date, userId)
    
    # Định dạng dữ liệu theo template
    return _format_patterns_result(data, start_date, end_date)


def _get_patterns_data(db: Session, start_date: datetime, end_date: datetime, userId: int) -> Dict[str, Any]:
    """Extract pattern data from database."""
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
    
    weekday_data = {int(day): count for day, count in tasks_by_weekday}
    hour_data = {int(hour): count for hour, count in tasks_by_hour}
    
    return {
        "weekday_data": weekday_data,
        "hour_data": hour_data
    }


def _format_patterns_result(data: Dict[str, Any], start_date: datetime, end_date: datetime) -> str:
    """Format pattern data into readable text using template."""
    weekday_data = data["weekday_data"]
    hour_data = data["hour_data"]
    
    # Tạo weekday patterns text
    weekday_patterns = ""
    for i in range(7):
        count = weekday_data.get(i, 0)
        day_name = get_weekday_name(i)
        weekday_patterns += f"\n• {day_name}: {count} task"
    
    # Tạo hourly patterns text
    hourly_patterns = ""
    peak_hours = []
    max_count = max(hour_data.values()) if hour_data else 0
    
    for hour in range(24):
        count = hour_data.get(hour, 0)
        if count > 0:
            hour_range = get_hour_range_string(hour)
            hourly_patterns += f"\n• {hour_range}: {count} task"
            if count >= max_count * 0.7:  # Peak hours
                peak_hours.append(f"{hour:02d}:00")
    
    # Tạo peak hours text
    peak_hours_text = ', '.join(peak_hours) if peak_hours else 'Không có pattern rõ ràng'
    
    # Tạo pattern insights
    pattern_insights = ""
    
    # Find most productive day
    if weekday_data:
        most_productive_day = max(weekday_data.items(), key=lambda x: x[1])
        day_name = get_weekday_name(most_productive_day[0])
        pattern_insights += f"\nNgày tạo task nhiều nhất: {day_name}"
    
    # Find peak hour
    if hour_data:
        peak_hour = max(hour_data.items(), key=lambda x: x[1])
        pattern_insights += f"\nGiờ tạo task nhiều nhất: {peak_hour[0]:02d}:00"
    
    # Áp dụng template
    return PATTERNS_TEMPLATE.format(
        days=(end_date - start_date).days,
        weekday_patterns=weekday_patterns,
        hourly_patterns=hourly_patterns,
        peak_hours=peak_hours_text,
        pattern_insights=pattern_insights
    )


def analyze_completion_rate(db: Session, start_date: datetime, end_date: datetime, userId: int) -> str:
    """Analyze task completion rates and trends."""
    
    # Lấy dữ liệu phân tích
    data = _get_completion_rate_data(db, start_date, end_date, userId)
    
    # Định dạng dữ liệu theo template
    return _format_completion_rate_result(data, start_date, end_date)


def _get_completion_rate_data(db: Session, start_date: datetime, end_date: datetime, userId: int) -> Dict[str, Any]:
    """Extract completion rate data from database."""
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
    
    return {
        "weekly_stats": weekly_stats,
        "priority_completion": priority_completion
    }


def _format_completion_rate_result(data: Dict[str, Any], start_date: datetime, end_date: datetime) -> str:
    """Format completion rate data into readable text using template."""
    weekly_stats = data["weekly_stats"]
    priority_completion = data["priority_completion"]
    
    # Tạo weekly trends text
    weekly_trends = ""
    for week in weekly_stats:
        weekly_trends += f"\n• Tuần {week['week_start']}: {week['completed']}/{week['total']} ({week['rate']:.1f}%)"
    
    # Tạo priority completion text
    priority_completion_text = ""
    for priority, total, completed in priority_completion:
        completed = completed or 0
        rate = get_completion_percentage(completed, total)
        priority_completion_text += f"\n• {priority.upper()}: {completed}/{total} ({rate:.1f}%)"
    
    # Tạo trend analysis text
    trend_analysis = ""
    if len(weekly_stats) >= 2:
        recent_rate = weekly_stats[-1]['rate']
        previous_rate = weekly_stats[-2]['rate']
        trend = recent_rate - previous_rate
        
        trend_analysis = "XU HƯỚNG GẦN ĐÂY:"
        if trend > 5:
            trend_analysis += f"\nHiệu suất đang cải thiện (+{trend:.1f}%)"
        elif trend < -5:
            trend_analysis += f"\nHiệu suất đang giảm ({trend:.1f}%)"
        else:
            trend_analysis += f"\nHiệu suất ổn định ({trend:+.1f}%)"
    
    # Áp dụng template
    return COMPLETION_RATE_TEMPLATE.format(
        days=(end_date - start_date).days,
        weekly_trends=weekly_trends,
        priority_completion=priority_completion_text,
        trend_analysis=trend_analysis
    )


def analyze_workload(db: Session, start_date: datetime, end_date: datetime, userId: int) -> str:
    """Analyze workload distribution and balance."""
    
    # Lấy dữ liệu phân tích
    data = _get_workload_data(db, start_date, end_date, userId)
    
    # Định dạng dữ liệu theo template
    return _format_workload_result(data, start_date, end_date)


def _get_workload_data(db: Session, start_date: datetime, end_date: datetime, userId: int) -> Dict[str, Any]:
    """Extract workload data from database."""
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
    
    # Creation counts
    creation_counts = [count for _, count in daily_creation]
    
    return {
        "daily_creation": daily_creation,
        "pending_by_priority": pending_by_priority,
        "tasks_with_due_dates": tasks_with_due_dates,
        "total_tasks": total_tasks,
        "creation_counts": creation_counts
    }


def _format_workload_result(data: Dict[str, Any], start_date: datetime, end_date: datetime) -> str:
    """Format workload data into readable text using template."""
    daily_creation = data["daily_creation"]
    pending_by_priority = data["pending_by_priority"]
    tasks_with_due_dates = data["tasks_with_due_dates"]
    total_tasks = data["total_tasks"]
    creation_counts = data["creation_counts"]
    
    # Tạo daily distribution text
    daily_distribution = ""
    if creation_counts:
        avg_daily = safe_average(creation_counts)
        max_daily = max(creation_counts)
        daily_distribution += f"\n• Trung bình: {avg_daily:.1f} task/ngày"
        daily_distribution += f"\n• Cao nhất: {max_daily} task/ngày"
        
        # Show recent days
        daily_distribution += "\n• 7 ngày gần nhất:"
        for date, count in daily_creation[-7:]:
            daily_distribution += f"\n  - {date}: {count} task"
    
    # Tạo pending tasks text
    pending_tasks = ""
    pending_total = 0
    for priority, count in pending_by_priority:
        pending_tasks += f"\n• {priority.upper()}: {count} task"
        pending_total += count
    
    pending_tasks += f"\n• TỔNG: {pending_total} task"
    
    # Tính deadline percentage
    deadline_percentage = get_completion_percentage(tasks_with_due_dates, total_tasks)
    
    # Tạo workload insights
    workload_insights = ""
    
    if pending_total > 20:
        workload_insights += "\nKhối lượng công việc quá tải! Cần ưu tiên và loại bỏ task không cần thiết."
    elif pending_total > 10:
        workload_insights += "\nKhối lượng công việc khá nhiều. Nên tập trung vào task ưu tiên cao."
    else:
        workload_insights += "\nKhối lượng công việc hợp lý, có thể quản lý tốt."
    
    if creation_counts and max(creation_counts) > safe_average(creation_counts) * 2:
        workload_insights += "\nCó ngày tạo quá nhiều task. Nên phân bổ đều hơn."
    
    if deadline_percentage < 30:
        workload_insights += "\nNên đặt deadline cho nhiều task hơn để quản lý thời gian tốt hơn."
    
    # Áp dụng template
    return WORKLOAD_TEMPLATE.format(
        days=(end_date - start_date).days,
        daily_distribution=daily_distribution,
        pending_tasks=pending_tasks,
        tasks_with_due_dates=tasks_with_due_dates,
        total_tasks=total_tasks,
        deadline_percentage=deadline_percentage,
        workload_insights=workload_insights
    )


def get_analytics_summary(db: Session, start_date: datetime, end_date: datetime, userId: int) -> Dict[str, Any]:
    """
    Get summary analytics data for dashboard or quick overview.
    
    Returns:
        Dictionary with key metrics
    """
    
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
    
    return result
