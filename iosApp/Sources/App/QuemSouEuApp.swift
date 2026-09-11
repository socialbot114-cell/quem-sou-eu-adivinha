import SwiftUI

@main struct QuemSouEuApp: App {
    @StateObject private var progress = ProgressStore()
    var body: some Scene { WindowGroup { RootView().environmentObject(progress) } }
}
