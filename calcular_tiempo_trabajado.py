from datetime import date, timedelta

time_worked = 0.0
salary__type = 'Por días'
working_hours = 8

start_date = date(2025, 11, 1)
end_date = date(2025, 11, 30)

days_of_week = [1]  # Lunes a Jueves

total_days = (end_date - start_date).days + 1
for day_offset in range(total_days):
    current_date = start_date + timedelta(days=day_offset)
    if current_date.isoweekday() in days_of_week:
        if salary__type == 'Por horas':
            time_worked += working_hours
        elif salary__type == 'Por días':
            time_worked += 1
        elif salary__type == 'Mensual fijo':
            time_worked = total_days / 30
            break

print(time_worked)
