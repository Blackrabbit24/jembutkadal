x = 0

for j in range(99):    
    x += 1
    y = 0    
    for i in range(9999):        
        y += 1
        # format x jadi 2 digit, y jadi 4 digit
        print(f"3314{x:02d}040799{y:04d}")
