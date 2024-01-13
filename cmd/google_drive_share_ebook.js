/**
 * Google drive folder file public share creator
 * For use on https://script.google.com/ platform (Google Apps Script)
 * Shares the folderID files and writes a db.json to the folder
 */
function share_folder_files() {
  var folderId = "1vRPsN2yBqSFVgVJTWarH43Sr7BLolZNS"; // library.pyrotechny.eu/ebooks
  var files = DriveApp.getFolderById(folderId).getFiles();
  var result = [];

  while (files.hasNext()) {
      var file = files.next();

      sharing = file.getSharingAccess();
      if (sharing != DriveApp.Access.ANYONE_WITH_LINK) {
        file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      }

      var entry = {
        filename: file.getName(),
		    view_url: "https://drive.google.com/file/d/" + file.getId() + "/view",
        download_url: "https://drive.google.com/uc?export=download&id=" + file.getId()
      };
  
      result.push(entry);
      Logger.log(entry["filename"] + " -> " + file.getId());
  };

  // Update or create db.json and share the file
  var file = null;
  files = DriveApp.getFolderById(folderId).getFilesByName("db.json");
  while (files.hasNext()) {
    file = files.next(); // NOTE: Only last file is updated, no duplicates are removed...
  }

  db_json_data = JSON.stringify(result);

  if (!file) {
    file = DriveApp.getFolderById(folderId).createFile("db.json", db_json_data, MimeType.PLAIN_TEXT);
    sharing = file.getSharingAccess();
    if (sharing != DriveApp.Access.ANYONE_WITH_LINK) {
        file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    }
    Logger.log("Created db.json");
  } else {
    file.setContent(db_json_data);
    Logger.log("Updated db.json");
  }

  download_url =  "https://drive.google.com/uc?export=view&id=" + file.getId();
  Logger.log("db.json located at " + download_url)
}
