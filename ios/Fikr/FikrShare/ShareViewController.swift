import UIKit
import SwiftUI
import UniformTypeIdentifiers

class ShareViewController: UIViewController {
    
    private var tagStore: TagStore?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        tagStore = TagStore()
        
        extractSharedContent { [weak self] url, title in
            guard let self = self else { return }
            
            DispatchQueue.main.async {
                self.presentShareView(url: url ?? "", title: title ?? "")
            }
        }
    }
    
    private func presentShareView(url: String, title: String) {
        guard let tagStore = tagStore else { return }
        
        let shareView = ShareView(
            tagStore: tagStore,
            url: url,
            title: title,
            onSave: { [weak self] in
                self?.completeRequest()
            },
            onCancel: { [weak self] in
                self?.cancelRequest()
            }
        )
        
        let hostingController = UIHostingController(rootView: shareView)
        hostingController.view.backgroundColor = .systemBackground
        
        addChild(hostingController)
        view.addSubview(hostingController.view)
        hostingController.view.translatesAutoresizingMaskIntoConstraints = false
        
        NSLayoutConstraint.activate([
            hostingController.view.topAnchor.constraint(equalTo: view.topAnchor),
            hostingController.view.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            hostingController.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            hostingController.view.trailingAnchor.constraint(equalTo: view.trailingAnchor)
        ])
        
        hostingController.didMove(toParent: self)
    }
    
    private func extractSharedContent(completion: @escaping (String?, String?) -> Void) {
        guard let extensionItems = extensionContext?.inputItems as? [NSExtensionItem] else {
            completion(nil, nil)
            return
        }
        
        for item in extensionItems {
            guard let attachments = item.attachments else { continue }
            
            for provider in attachments {
                if provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                    provider.loadItem(forTypeIdentifier: UTType.url.identifier) { data, error in
                        if let url = data as? URL {
                            let title = item.attributedContentText?.string
                            completion(url.absoluteString, title)
                            return
                        }
                        completion(nil, nil)
                    }
                    return
                }
                
                if provider.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) {
                    provider.loadItem(forTypeIdentifier: UTType.plainText.identifier) { data, error in
                        if let text = data as? String {
                            if text.hasPrefix("http://") || text.hasPrefix("https://") {
                                completion(text, nil)
                            } else {
                                completion(nil, text)
                            }
                            return
                        }
                        completion(nil, nil)
                    }
                    return
                }
            }
        }
        
        completion(nil, nil)
    }
    
    private func completeRequest() {
        extensionContext?.completeRequest(returningItems: nil)
    }
    
    private func cancelRequest() {
        extensionContext?.cancelRequest(withError: NSError(domain: "FikrShare", code: 0))
    }
}
