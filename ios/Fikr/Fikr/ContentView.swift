import SwiftUI

struct ContentView: View {
    @StateObject private var tagStore = TagStore()
    @State private var showingAddBookmark = false
    
    var body: some View {
        SettingsView(tagStore: tagStore)
            .sheet(isPresented: $showingAddBookmark) {
                BookmarkView(
                    tagStore: tagStore,
                    url: "",
                    title: "",
                    onSave: {
                        showingAddBookmark = false
                    },
                    onCancel: {
                        showingAddBookmark = false
                    }
                )
            }
    }
}

#Preview {
    ContentView()
}
