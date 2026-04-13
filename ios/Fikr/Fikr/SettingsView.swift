import SwiftUI

struct SettingsView: View {
    @ObservedObject var tagStore: TagStore
    
    @State private var serverURL: String = APIClient.getServerURL()
    @State private var isTestingConnection = false
    @State private var connectionStatus: ConnectionStatus?
    
    enum ConnectionStatus {
        case success
        case failure(String)
    }
    
    var body: some View {
        NavigationStack {
            Form {
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Server URL")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        TextField("http://localhost:8000", text: $serverURL)
                            .textContentType(.URL)
                            .keyboardType(.URL)
                            .autocapitalization(.none)
                            .autocorrectionDisabled()
                            .textFieldStyle(.roundedBorder)
                        
                        Text("Enter your Mac's Tailscale IP address with port 8000")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 4)
                    
                    Button {
                        saveAndTest()
                    } label: {
                        HStack {
                            Text("Save & Test Connection")
                            Spacer()
                            if isTestingConnection {
                                ProgressView()
                            } else if let status = connectionStatus {
                                switch status {
                                case .success:
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundColor(.green)
                                case .failure:
                                    Image(systemName: "xmark.circle.fill")
                                        .foregroundColor(.red)
                                }
                            }
                        }
                    }
                    .disabled(serverURL.isEmpty || isTestingConnection)
                    
                    if case .failure(let message) = connectionStatus {
                        Text(message)
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                } header: {
                    Text("Server Configuration")
                } footer: {
                    Text("Make sure your Mac's FastAPI server is running and both devices are on Tailscale.")
                }
                
                Section {
                    HStack {
                        Text("Cached Tags")
                        Spacer()
                        Text("\(tagStore.allTags.count)")
                            .foregroundColor(.secondary)
                    }
                    
                    if let lastFetched = tagStore.lastFetched {
                        HStack {
                            Text("Last Updated")
                            Spacer()
                            Text(lastFetched, style: .relative)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Button {
                        Task {
                            await tagStore.fetchTags()
                        }
                    } label: {
                        HStack {
                            Text("Refresh Tags")
                            Spacer()
                            if tagStore.isLoading {
                                ProgressView()
                            }
                        }
                    }
                    .disabled(tagStore.isLoading)
                    
                    if let error = tagStore.error {
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                } header: {
                    Text("Tag Cache")
                }
                
                Section {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("How to Use")
                            .font(.headline)
                        
                        VStack(alignment: .leading, spacing: 8) {
                            Label("Share any URL from Safari, Twitter, etc.", systemImage: "square.and.arrow.up")
                            Label("Select 'Fikr' from the share sheet", systemImage: "app.badge")
                            Label("Add tags with autocomplete", systemImage: "tag")
                            Label("Tap Save to bookmark", systemImage: "checkmark")
                        }
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 8)
                } header: {
                    Text("Instructions")
                }
            }
            .navigationTitle("Fikr Settings")
        }
    }
    
    private func saveAndTest() {
        APIClient.setServerURL(serverURL)
        isTestingConnection = true
        connectionStatus = nil
        
        Task {
            do {
                let success = try await APIClient.shared.testConnection()
                if success {
                    connectionStatus = .success
                    await tagStore.fetchTags()
                } else {
                    connectionStatus = .failure("Server returned error")
                }
            } catch {
                connectionStatus = .failure(error.localizedDescription)
            }
            isTestingConnection = false
        }
    }
}

#Preview {
    SettingsView(tagStore: TagStore())
}
