package main

import "core:fmt"
import "core:os"
import "core:encoding/json"
import "core:bufio"

// Basic Request structure from TS
Request :: struct {
	id:      int,
	method:  string,
	params:  json.Value,
}

// Basic Response structure to TS
Response :: struct {
	id:      int,
	result:  string,
	error:   string,
}

main :: proc() {
	fmt.println("RTA Odin Agent Started")

	// Setup buffered reader for stdin
	reader: bufio.Reader
	buffer: [1024]u8
	bufio.reader_init(&reader, os.stream_from_handle(os.stdin))

	for {
		// Read line from stdin (JSON-RPC request)
		line, err := bufio.reader_read_string(&reader, '\n', context.allocator)
		if err != nil {
			break
		}
		defer delete(line)

		// Simple JSON parse (placeholder)
		req: Request
		parse_err := json.unmarshal_string(line, &req)
		
		res: Response
		res.id = req.id

		if parse_err != nil {
			res.error = "Invalid JSON"
		} else {
			fmt.printf("Received method: %s\n", req.method)
			res.result = "OK"
		}

		// Marshall response back to TS
		res_json, _ := json.marshal(res)
		defer delete(res_json)
		
		fmt.printf("%s\n", res_json)
	}
}
