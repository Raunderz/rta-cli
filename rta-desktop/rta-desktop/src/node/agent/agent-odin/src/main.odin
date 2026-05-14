package main

import "core:fmt"
import client "shared/http/client"

main :: proc() {
    // 1. Fire a GET request
    res, err := client.get("https://github.com")
    if err != nil {
        fmt.printf("Request failed: %s\n", err)
        return
    }
    defer client.response_destroy(&res)

    fmt.printf("Status: %s\n", res.status)

    // 2. Read the response payload
    body, allocation, berr := client.response_body(&res)
    if berr != nil {
        fmt.printf("Error: %s\n", berr)
        return
    }
    defer client.body_destroy(body, allocation)

    fmt.println(body)
}
