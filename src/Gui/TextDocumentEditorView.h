#ifndef GUI_TEXTDOCUMENTEDITORVIEW_H
#define GUI_TEXTDOCUMENTEDITORVIEW_H

#include "PreCompiled.h"

#include <QPlainTextEdit>

#include <App/TextDocument.h>
#include <Gui/MDIView.h>
#include <Gui/Window.h>

namespace Gui {
	class GuiExport TextDocumentEditorView : public MDIView {
		Q_OBJECT

	public:
		TextDocumentEditorView(
				App::TextDocument* textDocument,
				QPlainTextEdit* editor, QWidget* parent);
		~TextDocumentEditorView();
		QPlainTextEdit* getEditor() const { return editor; }
		const char *getName() const { return "TextDocumentEditorView"; }
		bool onMsg(const char* msg, const char**);
		bool onHasMsg(const char* msg) const;
		bool canClose() override;

	private:
		void editObject(App::TextDocument* obj);
		void saveToObject();
		QPlainTextEdit* editor;
		App::TextDocument* textDocument;
	};
}

#endif
