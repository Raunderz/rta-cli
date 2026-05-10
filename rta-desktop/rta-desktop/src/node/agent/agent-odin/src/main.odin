package main

import "core:fmt"

x:i32 = 42
y:u64 = 100
z:int = 123

big_number := 1_000_000 // underscore for readability

pi:f32 = 3.14159
e:f64 = 2.71828

is_true:bool = true
is_false:bool = false

letter:rune = 'A'
emoji:rune = '😊'

name:string = "John Doe"
address:string = "123 Main St"
raw_string := `C:\Windows\System32` // raw string is different from normal string because it does not use escape characters and preserve formatting

length:= len(name)

result:= 10+5
diff:= 10-5
produ := 10*5
quotient := 10/5
remainder := 10%3

is_equal:= 10==10
not_equal := 10!=5
greater := 10>5
less_equal := 5<=10

and_result := true && false
or_result := true || false
not_result := !true

bit_and := 0b1010 & 0b1100 // 0b1000 -> 8
bit_or := 0b1010 | 0b1100
bit_xor := 0b1010 ~ 0b1100
bit_not := ~u8(0b1010)




main::proc(){
    fmt.println("Hello World")
}

