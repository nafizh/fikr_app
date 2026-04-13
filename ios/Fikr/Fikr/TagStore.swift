import Foundation
import SwiftUI

@MainActor
class TagStore: ObservableObject {
    @Published var allTags: [String] = []
    @Published var isLoading = false
    @Published var error: String?
    @Published var lastFetched: Date?
    
    private static let cacheKey = "fikr_cached_tags"
    private static let cacheTimestampKey = "fikr_tags_cache_timestamp"
    private static let cacheExpiry: TimeInterval = 3600
    
    init() {
        loadCachedTags()
    }
    
    private func loadCachedTags() {
        if let cached = UserDefaults.standard.stringArray(forKey: Self.cacheKey) {
            allTags = cached
        }
        if let timestamp = UserDefaults.standard.object(forKey: Self.cacheTimestampKey) as? Date {
            lastFetched = timestamp
        }
    }
    
    private func cacheTags(_ tags: [String]) {
        UserDefaults.standard.set(tags, forKey: Self.cacheKey)
        UserDefaults.standard.set(Date(), forKey: Self.cacheTimestampKey)
        lastFetched = Date()
    }
    
    private func isCacheExpired() -> Bool {
        guard let lastFetched = lastFetched else { return true }
        return Date().timeIntervalSince(lastFetched) > Self.cacheExpiry
    }
    
    func fetchTagsIfNeeded() async {
        if !allTags.isEmpty && !isCacheExpired() {
            return
        }
        await fetchTags()
    }
    
    func fetchTags() async {
        isLoading = true
        error = nil
        
        do {
            let tags = try await APIClient.shared.fetchTags()
            allTags = tags.sorted()
            cacheTags(allTags)
            isLoading = false
        } catch {
            self.error = error.localizedDescription
            isLoading = false
        }
    }
    
    func filter(query: String) -> [String] {
        let trimmed = query.trimmingCharacters(in: .whitespaces).lowercased()
        guard !trimmed.isEmpty else { return [] }
        
        var prefixMatches: [String] = []
        var containsMatches: [String] = []
        
        for tag in allTags {
            let lowercased = tag.lowercased()
            if lowercased.hasPrefix(trimmed) {
                prefixMatches.append(tag)
            } else if lowercased.contains(trimmed) {
                containsMatches.append(tag)
            }
        }
        
        let combined = prefixMatches + containsMatches
        return Array(combined.prefix(10))
    }
    
    func addNewTag(_ tag: String) {
        let normalized = tag.trimmingCharacters(in: .whitespaces).lowercased()
        guard !normalized.isEmpty else { return }
        
        if !allTags.contains(normalized) {
            allTags.append(normalized)
            allTags.sort()
            cacheTags(allTags)
        }
    }
}
