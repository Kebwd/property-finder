from datetime import datetime, timedelta

start_date = datetime.now() - timedelta(days=14)
end_date = datetime.now()

print(f'Spider searches from: {start_date.strftime("%d/%m/%Y")} to {end_date.strftime("%d/%m/%Y")}')
print(f'Today is: {datetime.now().strftime("%d/%m/%Y")}')
print(f'August 19, 2025 in search range: {"06/08/2025" <= "19/08/2025" <= "20/08/2025"}')
