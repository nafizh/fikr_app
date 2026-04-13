import Foundation

actor APIClient {
    static let shared = APIClient()
    
    private let session: URLSession
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder
    
    private static let serverURLKey = "fikr_server_url"
    private static let defaultServerURL = "http://100.64.0.1:8000"
    
    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: config)
        self.encoder = JSONEncoder()
        self.decoder = JSONDecoder()
    }
    
    static func getServerURL() -> String {
        UserDefaults.standard.string(forKey: serverURLKey) ?? defaultServerURL
    }
    
    static func setServerURL(_ url: String) {
        UserDefaults.standard.set(url, forKey: serverURLKey)
    }
    
    private func baseURL() throws -> URL {
        let urlString = Self.getServerURL()
        guard !urlString.isEmpty, let url = URL(string: urlString) else {
            throw APIError.noServerConfigured
        }
        return url
    }
    
    func fetchTags() async throws -> [String] {
        let url = try baseURL().appendingPathComponent("/api/tags")
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(URLError(.badServerResponse))
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        do {
            let tagsResponse = try decoder.decode(TagsResponse.self, from: data)
            return tagsResponse.tags
        } catch {
            throw APIError.decodingError(error)
        }
    }
    
    func saveBookmark(url: String, title: String?, tags: [String], description: String?) async throws -> BookmarkResponse {
        let apiURL = try baseURL().appendingPathComponent("/api/add")
        
        var request = URLRequest(url: apiURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let tagsString = tags.joined(separator: " ")
        let bookmarkRequest = BookmarkRequest(
            url: url,
            title: title,
            tags: tagsString.isEmpty ? nil : tagsString,
            description: description
        )
        
        request.httpBody = try encoder.encode(bookmarkRequest)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(URLError(.badServerResponse))
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        do {
            return try decoder.decode(BookmarkResponse.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }
    
    func suggestTags(url: String, title: String?, description: String?, existingTags: [String]?) async throws -> [String] {
        let apiURL = try baseURL().appendingPathComponent("/api/suggest-tags")
        
        var request = URLRequest(url: apiURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let suggestRequest = SuggestTagsRequest(
            url: url,
            title: title,
            description: description,
            page_content: nil,
            existing_tags: existingTags,
            max_tags: 8
        )
        
        request.httpBody = try encoder.encode(suggestRequest)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(URLError(.badServerResponse))
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        do {
            let suggestResponse = try decoder.decode(SuggestTagsResponse.self, from: data)
            return suggestResponse.tags
        } catch {
            throw APIError.decodingError(error)
        }
    }
    
    func testConnection() async throws -> Bool {
        let url = try baseURL().appendingPathComponent("/api/tags")
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 5
        
        let (_, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            return false
        }
        
        return httpResponse.statusCode == 200
    }
}
