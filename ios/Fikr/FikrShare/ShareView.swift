import SwiftUI

struct ShareView: View {
    @ObservedObject var tagStore: TagStore
    
    let url: String
    let title: String
    let onSave: () -> Void
    let onCancel: () -> Void
    
    var body: some View {
        BookmarkView(
            tagStore: tagStore,
            url: url,
            title: title,
            onSave: onSave,
            onCancel: onCancel
        )
    }
}
