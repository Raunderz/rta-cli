package main

import "core:fmt"

main :: proc() {

	x: i32 = 42
	y: u64 = 100
	z: int = 123

	big_number := 1_000_000 // underscore for readability

	pi: f32 = 3.14159
	e: f64 = 2.71828

	is_true: bool = true
	is_false: bool = false

	letter: rune = 'A'
	emoji: rune = '😊'

	name: string = "John Doe"
	address: string = "123 Main St"
	raw_string := `C:\Windows\System32` // raw string is different from normal string because it does not use escape characters and preserve formatting

	length := len(name)

	result := 10 + 5
	diff := 10 - 5
	produ := 10 * 5
	quotient := 10 / 5
	remainder := 10 % 3

	is_equal := 10 == 10
	not_equal := 10 != 5
	greater := 10 > 5
	less_equal := 5 <= 10

	and_result := true && false
	or_result := true || false
	not_result := !true

	bit_and := 0b1010 & 0b1100 // 0b1000 -> 8
	bit_or := 0b1010 | 0b1100
	bit_xor := 0b1010 ~ 0b1100
	bit_not := ~u8(0b1010)

	some_number := 42
	some_text := "Hello"

	explicit_int: int = 42
	explicit_float: f64 = 3.14

	// constants defined by ::
	PI :: 3.14159
	MESSAGE :: "this is a constant"

	// typed constants
	TYPED_CONSTANT: f32 : 2.71828

	// multiple assignment
	a, b := 10, 20
	a, b = b, a // swap

	// fixed size array
	numbers: [5]int = {1, 2, 3, 4, 5}
	chars: [3]rune = {'A', 'B', 'C'} // rune datatype represents unicode character

	// array with inferred size
	inferred := [?]int{10, 20, 30, 40}

	//zero initialized array
	zeros: [10]int

	// acccessing array elemnts
	first := numbers[0]
	last := numbers[4]
	array_length := len(numbers)

	// slices
	slice: []int = {1, 2, 3, 4, 5} // slice literal - creates dynamic array
	full_slice := numbers[:]

	array_slice := numbers[1:3] // lower inclusive upper exclusive

	dynamic_array: [dynamic]int // can grow and shrink - different from slice (dynamic array is a type, slice is a view)

	append(&dynamic_array, 1)
	append(&dynamic_array, 2, 3, 4) // append multiple elements

	defer delete(dynamic_array) // cleanup

	age := 25
	if age >= 18 {
		fmt.println("Adult")
	} else if age >= 13 {
		fmt.println("Teenager")
	} else {
		fmt.println("Child")
	}

	// for loops - odin's only loop construct
	for i := 0; i < 10; i += 1 {
		fmt.println("i", i)
	}

	// conditions are optional
	for {
		fmt.println("This will loop forever.")
	}

	for i in 0 ..< 5 {
		fmt.println(i) // i am never gonna use ts
	}

	for i in 0 ..= 4 {
		fmt.println(i) // neither will i use this
	}

	// iterating over arrays/slices with index
	numbers_array := [3]int{10, 20, 30}
	for value, index in numbers_array {
		fmt.printf("index %d: Value %d\n", index, value)
	}

	// iterating over just values
	for value in numbers_array {
		fmt.println(value)
	}

	// Switch statements
	day := "Monday"
	switch day {
	case "Monday", "Tuesday", "Wednesday", "Thursday", "Friday":
		fmt.println("Weekday")
	case "Saturday", "Sunday":
		fmt.println("Weekend")
	case:
		// Default case
		fmt.println("Unknown day")
	}

    // SWITCH no condition
    switch{
        case age < 13:
            fmt.println("Child")
        case age < 20:
            fmt.println("Teenager")
        case age < 60:
            fmt.println("Adult")
        case:
            fmt.println("Senior")
    }

    // procedures / functiomns

	fmt.println("Hello World")
}
