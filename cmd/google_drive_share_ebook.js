/**
 * Google drive folder file public share creator
 * For use on https://script.google.com/ platform
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
        url: "https://drive.google.com/uc?export=view&id=" + file.getId(),
        download_url: "https://drive.google.com/uc?export=view&id=" + file.getId() + "&export=download"
      };
      result.push(entry);
  };

  data = JSON.stringify(result);
  Logger.log(data);

  // Create db.json and share the file
  DriveApp.getFolderById(folderId).createFile("db.json", data, MimeType.PLAIN_TEXT);
  files = DriveApp.getFolderById(folderId).getFilesByName("db.json");
  while (files.hasNext()) {
      var file = files.next();
      if (file.getName() != "db.json") {
        continue;
      }

      sharing = file.getSharingAccess();
      if (sharing != DriveApp.Access.ANYONE_WITH_LINK) {
        file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      }

      download_url =  "https://drive.google.com/uc?export=view&id=" + file.getId() + "&export=download";
      Logger.log("db.json: " + download_url)
  }
}

share_folder_files();
