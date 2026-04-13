import Foundation

struct TagsResponse: Codable {
    let tags: [String]
}

struct BookmarkRequest: Codable {
    let url: String
    let title: String?
    let tags: String?
    let description: String?
}

struct BookmarkResponse: Codable {
    let status: String
    let action: String?
    let url: String?
}

struct SuggestTagsRequest: Codable {
    let url: String
    let title: String?
    let description: String?
    let page_content: String?
    let existing_tags: [String]?
    let max_tags: Int
}

struct SuggestTagsResponse: Codable {
    let tags: [String]
}

enum APIError: Error, LocalizedError {
    case invalidURL
    case networkError(Error)
    case serverError(Int)
    case decodingError(Error)
    case noServerConfigured
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .serverError(let code):
            return "Server error: \(code)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        case .noServerConfigured:
            return "No server configured. Open Fikr app to set server URL."
        }
    }
}
