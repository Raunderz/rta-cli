package main

import "core:fmt"
import "core:os"
import "core:encoding/json"
import "core:bufio"
import "core:io"

Request :: struct {
    id:      int,
    method:  string,
    params:  json.Value,
}

Response :: struct {
    id:      int,
    result:  string,
    error:   string,
}

main :: proc() {
    fmt.println("Odin Agent Started")

    reader: bufio.Reader
    // In dev-2026-05, os.stdin is a Handle. os.to_stream(os.stdin) converts it to an io.Stream.
    bufio.reader_init(&reader, os.to_stream(os.stdin))

    for {
        line, err := bufio.reader_read_string(&reader, '\n', context.allocator)
        if err != io.Error.None { // Standard error check
            break
        }
        defer delete(line)

        req: Request
        // Ensure you pass the pointer &req
        parse_err := json.unmarshal_string(line, &req)
        
        res: Response
        res.id = req.id

        if parse_err != nil {
            res.error = "Invalid JSON"
        } else {
            // Using eprintf so this doesn't mess up your JSON output if you pipe it
            fmt.eprintf("Received method: %s\n", req.method)
            res.result = "OK"
        }

        res_json, _ := json.marshal(res)
        defer delete(res_json)
        
        fmt.printf("%s\n", res_json)
    }
}
