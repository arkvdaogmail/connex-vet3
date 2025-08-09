// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DocumentNotary {
    event DocumentNotarized(
        address indexed sender,
        string documentHash,
        string comment
    );

    function notarizeDocument(
        string memory documentHash, 
        string memory comment
    ) public {
        emit DocumentNotarized(
            msg.sender,
            documentHash,
            comment
        );
    }
}
