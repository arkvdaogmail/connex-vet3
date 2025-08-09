// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DocumentNotaryOptimized {
    // Packed struct for gas efficiency
    struct Document {
        bytes32 hash;
        uint32 timestamp;
        address notary;
    }
    
    mapping(bytes32 => Document) public documents;
    
    event DocumentNotarized(
        bytes32 indexed hash,
        address indexed notary,
        uint32 timestamp
    );
    
    event BatchNotarized(
        address indexed notary,
        uint256 count,
        uint32 timestamp
    );

    // Single document notarization
    function notarizeDocument(bytes32 documentHash) external {
        require(documents[documentHash].timestamp == 0, "Already notarized");
        
        uint32 timestamp = uint32(block.timestamp);
        documents[documentHash] = Document({
            hash: documentHash,
            timestamp: timestamp,
            notary: msg.sender
        });
        
        emit DocumentNotarized(documentHash, msg.sender, timestamp);
    }
    
    // Batch notarization for cost efficiency
    function notarizeDocumentsBatch(bytes32[] calldata documentHashes) external {
        require(documentHashes.length > 0, "Empty batch");
        require(documentHashes.length <= 50, "Batch too large"); // Prevent gas limit issues
        
        uint32 timestamp = uint32(block.timestamp);
        
        for (uint256 i = 0; i < documentHashes.length; i++) {
            bytes32 hash = documentHashes[i];
            require(documents[hash].timestamp == 0, "Document already notarized");
            
            documents[hash] = Document({
                hash: hash,
                timestamp: timestamp,
                notary: msg.sender
            });
            
            emit DocumentNotarized(hash, msg.sender, timestamp);
        }
        
        emit BatchNotarized(msg.sender, documentHashes.length, timestamp);
    }
    
    // View function to check if document is notarized
    function isNotarized(bytes32 documentHash) external view returns (bool) {
        return documents[documentHash].timestamp != 0;
    }
    
    // Get document details
    function getDocument(bytes32 documentHash) external view returns (
        bytes32 hash,
        uint32 timestamp,
        address notary
    ) {
        Document memory doc = documents[documentHash];
        return (doc.hash, doc.timestamp, doc.notary);
    }
}

