def es_primo (n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

max=1000
sum=0
i=0
while i < max:
    if sum < max-i:
        print(sum)
        if es_primo(i):
            sum += i
        i= i + 1        
    else:
        break   
            
print("La suma de los números primos menores que", max, "es:", sum)