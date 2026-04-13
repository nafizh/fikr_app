import SwiftUI

struct BookmarkView: View {
    @ObservedObject var tagStore: TagStore
    
    let initialURL: String
    let initialTitle: String
    let onSave: () -> Void
    let onCancel: () -> Void
    
    @State private var url: String
    @State private var title: String
    @State private var description: String = ""
    @State private var selectedTags: [String] = []
    @State private var tagInput: String = ""
    @State private var showingSuggestions = false
    @State private var isSaving = false
    @State private var isSuggestingTags = false
    @State private var saveError: String?
    @State private var showSuccess = false
    
    @FocusState private var isTagInputFocused: Bool
    
    init(
        tagStore: TagStore,
        url: String,
        title: String,
        onSave: @escaping () -> Void,
        onCancel: @escaping () -> Void
    ) {
        self.tagStore = tagStore
        self.initialURL = url
        self.initialTitle = title
        self.onSave = onSave
        self.onCancel = onCancel
        self._url = State(initialValue: url)
        self._title = State(initialValue: title)
    }
    
    private var filteredTags: [String] {
        tagStore.filter(query: tagInput)
            .filter { !selectedTags.contains($0) }
    }
    
    var body: some View {
        NavigationStack {
            Form {
                Section("URL") {
                    TextField("URL", text: $url)
                        .textContentType(.URL)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                        .autocorrectionDisabled()
                }
                
                Section("Title") {
                    TextField("Title", text: $title)
                }
                
                Section("Description") {
                    TextField("Description (optional)", text: $description, axis: .vertical)
                        .lineLimit(3...6)
                }
                
                Section {
                    VStack(alignment: .leading, spacing: 12) {
                        if !selectedTags.isEmpty {
                            FlowLayout(spacing: 8) {
                                ForEach(selectedTags, id: \.self) { tag in
                                    TagChip(tag: tag) {
                                        withAnimation(.easeInOut(duration: 0.2)) {
                                            selectedTags.removeAll { $0 == tag }
                                        }
                                    }
                                }
                            }
                        }
                        
                        HStack {
                            TextField("Add tag...", text: $tagInput)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                                .focused($isTagInputFocused)
                                .onSubmit {
                                    addCurrentInput()
                                }
                                .onChange(of: tagInput) { _, newValue in
                                    showingSuggestions = !newValue.isEmpty
                                }
                            
                            if !tagInput.isEmpty {
                                Button {
                                    addCurrentInput()
                                } label: {
                                    Image(systemName: "plus.circle.fill")
                                        .foregroundColor(.blue)
                                }
                            }
                        }
                        
                        if showingSuggestions && !filteredTags.isEmpty {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 8) {
                                    ForEach(filteredTags, id: \.self) { tag in
                                        Button {
                                            addTag(tag)
                                        } label: {
                                            Text(tag)
                                                .font(.subheadline)
                                                .padding(.horizontal, 12)
                                                .padding(.vertical, 6)
                                                .background(Color.blue.opacity(0.1))
                                                .foregroundColor(.blue)
                                                .cornerRadius(16)
                                        }
                                    }
                                }
                            }
                            .frame(height: 36)
                        }
                    }
                } header: {
                    HStack {
                        Text("Tags")
                        Spacer()
                        Button {
                            suggestTags()
                        } label: {
                            HStack(spacing: 4) {
                                if isSuggestingTags {
                                    ProgressView()
                                        .scaleEffect(0.7)
                                } else {
                                    Image(systemName: "wand.and.stars")
                                }
                                Text("AI Suggest")
                            }
                            .font(.caption)
                        }
                        .disabled(isSuggestingTags)
                    }
                }
                
                if let error = saveError {
                    Section {
                        Text(error)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Add Bookmark")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        onCancel()
                    }
                    .disabled(isSaving)
                }
                
                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        saveBookmark()
                    } label: {
                        if isSaving {
                            ProgressView()
                        } else {
                            Text("Save")
                        }
                    }
                    .disabled(url.isEmpty || isSaving)
                }
            }
            .overlay {
                if showSuccess {
                    VStack {
                        Spacer()
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            Text("Saved!")
                        }
                        .padding()
                        .background(.ultraThinMaterial)
                        .cornerRadius(10)
                        Spacer()
                    }
                }
            }
            .task {
                await tagStore.fetchTagsIfNeeded()
            }
        }
    }
    
    private func addTag(_ tag: String) {
        let normalized = tag.trimmingCharacters(in: .whitespaces).lowercased()
        guard !normalized.isEmpty, !selectedTags.contains(normalized) else { return }
        
        withAnimation(.easeInOut(duration: 0.2)) {
            selectedTags.append(normalized)
        }
        tagInput = ""
        showingSuggestions = false
    }
    
    private func addCurrentInput() {
        let trimmed = tagInput.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        
        addTag(trimmed)
        tagStore.addNewTag(trimmed)
    }
    
    private func suggestTags() {
        isSuggestingTags = true
        
        Task {
            do {
                let suggested = try await APIClient.shared.suggestTags(
                    url: url,
                    title: title.isEmpty ? nil : title,
                    description: description.isEmpty ? nil : description,
                    existingTags: selectedTags.isEmpty ? nil : selectedTags
                )
                
                for tag in suggested {
                    if !selectedTags.contains(tag) {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            selectedTags.append(tag)
                        }
                    }
                }
            } catch {
                saveError = "AI suggestion failed: \(error.localizedDescription)"
            }
            
            isSuggestingTags = false
        }
    }
    
    private func saveBookmark() {
        isSaving = true
        saveError = nil
        
        Task {
            do {
                _ = try await APIClient.shared.saveBookmark(
                    url: url,
                    title: title.isEmpty ? nil : title,
                    tags: selectedTags,
                    description: description.isEmpty ? nil : description
                )
                
                showSuccess = true
                
                try? await Task.sleep(nanoseconds: 800_000_000)
                
                onSave()
            } catch {
                saveError = error.localizedDescription
                isSaving = false
            }
        }
    }
}

struct TagChip: View {
    let tag: String
    let onRemove: () -> Void
    
    var body: some View {
        HStack(spacing: 4) {
            Text(tag)
                .font(.subheadline)
            
            Button(action: onRemove) {
                Image(systemName: "xmark.circle.fill")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(Color.blue.opacity(0.15))
        .foregroundColor(.primary)
        .cornerRadius(16)
    }
}

struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = layout(proposal: proposal, subviews: subviews)
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = layout(proposal: proposal, subviews: subviews)
        
        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(x: bounds.minX + result.positions[index].x,
                                       y: bounds.minY + result.positions[index].y),
                          proposal: .unspecified)
        }
    }
    
    private func layout(proposal: ProposedViewSize, subviews: Subviews) -> (size: CGSize, positions: [CGPoint]) {
        let maxWidth = proposal.width ?? .infinity
        
        var positions: [CGPoint] = []
        var currentX: CGFloat = 0
        var currentY: CGFloat = 0
        var lineHeight: CGFloat = 0
        var maxX: CGFloat = 0
        
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            
            if currentX + size.width > maxWidth && currentX > 0 {
                currentX = 0
                currentY += lineHeight + spacing
                lineHeight = 0
            }
            
            positions.append(CGPoint(x: currentX, y: currentY))
            
            lineHeight = max(lineHeight, size.height)
            currentX += size.width + spacing
            maxX = max(maxX, currentX)
        }
        
        return (CGSize(width: maxX, height: currentY + lineHeight), positions)
    }
}

#Preview {
    BookmarkView(
        tagStore: TagStore(),
        url: "https://example.com",
        title: "Example Page",
        onSave: {},
        onCancel: {}
    )
}
