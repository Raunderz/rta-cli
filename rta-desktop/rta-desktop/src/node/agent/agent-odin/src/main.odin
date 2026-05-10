package main
// every .odin file starts with package declaration

import "core:fmt"
// import core libraries
import "core:string"
import "core:os"

// import with alias
import str "core:string" // what this does is instead of typing "core:string" we can just type "str"

// import frmo vendor packages ( external lib)
// import vendor::raylib

// compile time constants
ENABLE_LOGGING :: #config(ENABLE_LOGGING,false)

// generics ( parametric polymoprhism ) what this does is that it allows us to write code that can work with multiple types
// kind of like templates in c++ but much better and type safe
Generic_Array:: struct($T:typeid){
    data: []T, // i dont understand a single word of this
}


// built in data structures
File_Mode :: enum {
    READ,
    WRITE,
    EXECUTE,
}

add::proc(a:$T,b:T)-> T{
    return a+b
    // explanation : this is a generic procedure that can work with multiple types , as you can see we have $T:typeid which is a type parameter , it can be any type
    // example : let result := add(1,2) // here $T is inferred as int , let result := add(1.0,2.0) // here $T is inferred as f32
    // is it like auto in cpp ?? the answer is kinda no , because it is type safe
    // but its kinda like templates in c++ 
    // i hope you understood , yeah sure gemini i do i guess , lol 
}


// structs
Person::struct{
    name:string,
    age:int,
    height:f32,
}

// struct instances
person1 := Person{
    name= "alice",
    age = 30,
    height=5.6,
}

// partial initialiation
person2:=Person{
    name="bob",
    // age and height defeault to 0
}

// enums and unions
Colour :: enum{
    RED,
    GREEN,
    BLUE,
    YELLOW,
}

Status::enum u8{
    // enums with explicit values
    OK = 0,
    ERROR = 1,
    WARNING = 2,
}

Value :: union{int,bool} // the c++ equivalent of this is std::variant<int,bool> , basically it can hold either int or bool at a time but not both

v:Value // in odin , unioons have a default state of `nil`



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
	// for {
	// 	fmt.println("This will loop forever.")
	// }

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
    // doing outside main function

// Using the procedure
    sum := add(5, 3)                    // 8
    quotient_good, ok := divide(10, 2)       // 5, true
    quotient_bad, ok_bad := divide(10, 0) // 0, false

    // proceure grouping
    greet("John") // calls greet_string
    greet() // calls greet_nothing

    // Variadic Procedures
    sum_result:=sum_all(1,2,3,4,5)
    fmt.printf("%d", sum_result) // sum = 15
    fmt.printf("%d", sum_all()) // sum = 0


    // accessing struct fields
    fmt.printf("%s", person1.name)
    fmt.printf("%d", person1.age)
    fmt.printf("%f", person1.height)

    fmt.printf("%s", person2.name)
    fmt.printf("%d", person2.age)
    fmt.printf("%f", person2.height)

    // modifying struct fields
    person1.age = 31

    celebrate_birthday(&person1)

    my_color := Colour.RED

    // pattern matchig with unions
    switch _ in v {
        case int: fmt.println("int")
        case bool: fmt.println("bool")
        case:
            fmt.println("Unknown")
    }

    // map declaration
    scores:map[string]int // in c++ it would be std::map<string,int>

    scores = make(map[string]int) // initialize map , idk why we need to do this but we need to do this
    defer delete(scores) // clean up when done

    // add key value pairs
    scores["alice"] = 95
    scores["bob"] = 87
    scores["Charlie"] = 92

    // access values
    alice_score := scores["alice"]
    
    // check if key exists
    bob_score, exists := scores["bob"]
    if exists{
        fmt.printf("bob's scores: %d\n",bob_score)
    }

    // iterate over map
    for name,score in scores {
        fmt.printf("%s: %d\n",name,score)
    }

    // pointers and memory management
    // pointers
    number := 42
    number_ptr := &number
    value := number_ptr^ // dereferencing 

    fmt.printf("value: %d, address:%p\n",value,number_ptr)

    // dynamic memory allocation
    // new() allocaed and reutns a pointer
    int_ptr := new(int)
    int_ptr^=100
    defer free(int_ptr) // clean up memeory

    // make() for complex types
    my_slice:=make([]int,5) // create slice with length 5 , reminder slice is a view , so this will make a array that will look like this {0,0,0,0,0}
    defer delete(my_slice)

    // error handling
    // oding uses multiple return values for error handling
    // wil lmake th function outisde
    content,success:=read_file("myfile.txt")
    if !success{
        fmt.printf("failed to read file")
    }else{
        fmt.printf("file content: %s\n",content)
    }


    // using imported prorcudes
    text:="Hellow rold"
    upper_text := strings.to_upper(text)
    // using alias
    upper_text_alias := str.to_upper(text)
    fmt.println(upper_text)


    // compile time conditionals
    when ODIN_OS == .Windows{
        fmt.println("Windows")
    }else when ODIN_OS == .Linux{
        fmt.println("Linux")
    }else{
        fmt.println("Mac")
    }


    when ENABLE_LOGGING{
        fmt.println("Logging is enabled")
    }

    sum_int := add(10,20) // T becomes int
    sum_float := add(1.0,2.0) // T becomes f32

    permissions: bit_set[File_Mode] // idk yet
    // right now th ebitset looks like {.}
    permissions += {.READ,.WRITE} // add values to bitset
    permissions -= {.WRITE}
    has_read := .READ in permissions
    is_readonly := permissions == {.READ}
    is_write_only := permissions == {.WRITE}
    

    // complex numbers
    z1 := complex64(3+4i)
    z2 := complex64(1-2i)
    sum_comp := z1+z2
    magnitude := abs(z1)


    // matrices for linear algebra
    transform:= matrix[3,3]f32{
        1,0,5, // trnalstate to x= 5
        0,1,3, // y = 3
        0,0,1, // homoegnous coordinate
    }

    point := [3]f32{10,20,1} // this is a 2d point (10,20) with 1 as the homoegnous coordinate , homo coord means it can be anything i guess but most commonly used for points in space
    
    transformed := transform*point
    // quaternion for 3d rotation , wtf is quaternions ? 
    identity_rot := quaternion(w=1,x=0,y=0,z=0) // no rotation
    rotation_90_z := quaternion(w=0.707,x=0,y=0,z=0.707) // 90 degree around z


    // context system and defer . last topic yaya
    // odin has an implicit contex ssytem that makes it easy to use
    // idk what that means
    // temporary allocations in loops without manual cleanip
    // i will make the fucntion extetnally




	fmt.println("\nHello World")
}

// context system and defer
process_files :: proc(filenames:[]string){ // []string makes a empty slice while ...string wouldve made a array of strings, difference : []<T> vs ...T : if its just <T> it means a empty slice and you can add as many as you want, while ...T means it will take 0 or more arguments
    
    defer free_all(context.temp_allocator) // clear the arena wehn done
    for filename in filenames {
        // each iteration allocates temporaty data
        data:=make([]u8,1024,context.temp_allocator) // no defer is needed here
        fmt.printf("processing %s with %d bytes\n",filename,len(data))
        // after the loop finishes the defer will free the temp_allocator and all the data that was allocated in it
        // no invidual clean up needed
    }
}
// defer ensures cleanup on scope exit
resource_example :: proc(){
    buffer:=make([]u8,1024)
    defer delete(buffer) // clean up
    // using the buffer 
}



// and now i have completed the odin basic tutorial 
// inmy not so great expereience in world of coding, i think this resembels golang a lot
// now the main reason to learn this was to make the ai agent , for RTA , and since i wanted to make it in some low level language ( its currently in python ) for speed and less size , i googled , ofc i could have picked up c++ as i already know it well but i feel like i will keep c++ for leetcode and other stuff only , for dev i'll try new languages. like after odin i think i will port this to zig, alr done bye


// add::proc(a:int,b:int)->int{ // add is function name, proc means procedure or function, params passed with their typed , -> int means it will send int as return
//     return a+b
// } 
// commenting out since we T now

// with multiple return values
divide::proc(a:int,b:int)->(int,bool){
    if b==0{
        return 0,false
    }
    return a/b,true
}

// someting similar to overloading can be mimicked by using procedure groups
greet_string :: proc(name:string){
    fmt.printf("Hello %s\n",name)
}

greet_nothing :: proc(){
    greet_string("World")
}

greet::proc{ // procedure group
    greet_string,
    greet_nothing,
}

// variadivc producees ( variable number of arguments)
sum_all::proc(numbers:..int) -> int{ // numbers is of type slice of int
    total:=0
    for number in numbers{
        total+=number
    }
    return total
}

// procedure that works with structs
celebrate_birthday::proc(person:^Person){
    // ^ means pointer btw
    person.age +=1
    fmt.printf("Happy Birthday %s\n", person.name)
}

read_file :: proc(filename:string)->(string,bool){
    // simulate file reading
    if filename == ""{
        return "",false
    }
    return "file content",true
}

// common pattern with or_return
parse_number :: proc(s:string) -> (int,bool){
    if s=="42"{
        return 42,true
    }
    return 0,false
}

example_with_error_handling :: proc() -> bool {
    // or_return automatically returns false if the second value is false
    num := parse_number("42") or_return // what this does is checks if the second value is false , if it is false , it will return false from the current procedure
    // i find it very useless
    fmt.printf("Parsed number: %d\n",num)
    return true
}